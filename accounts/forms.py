from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from .models import Address, Profile


class PremiumFormMixin:
    input_class = "form-control premium-input"

    def apply_premium_styles(self):
        for field in self.fields.values():
            base_class = field.widget.attrs.get("class", "").strip()
            field.widget.attrs["class"] = f"{base_class} {self.input_class}".strip()


def generate_unique_username(email):
    base = slugify(email.split("@")[0]) or "user"
    candidate = base[:150]
    index = 1
    while User.objects.filter(username__iexact=candidate).exists():
        suffix = str(index)
        candidate = f"{base[:150 - len(suffix) - 1]}-{suffix}"
        index += 1
    return candidate


class RegistrationForm(PremiumFormMixin, UserCreationForm):
    first_name = forms.CharField(max_length=150, label="Name")
    last_name = forms.CharField(max_length=150, required=False, label="Last name")
    email = forms.EmailField(label="Email address")
    phone_number = forms.CharField(max_length=20, label="Phone number")

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone_number", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].widget.attrs.update({"placeholder": "Your name"})
        self.fields["last_name"].widget.attrs.update({"placeholder": "Optional"})
        self.fields["email"].widget.attrs.update({"placeholder": "Enter your email"})
        self.fields["phone_number"].widget.attrs.update({"placeholder": "Enter your phone number"})
        self.fields["password1"].widget.attrs.update({"placeholder": "Create a password"})
        self.fields["password2"].widget.attrs.update({"placeholder": "Confirm your password"})
        self.fields["phone_number"].help_text = "Use an active phone number for order updates."
        self.fields["password2"].help_text = "Re-enter the same password to confirm your account security."
        self.apply_premium_styles()

    def clean_first_name(self):
        name = self.cleaned_data["first_name"].strip()
        if len(name) < 2:
            raise ValidationError("Enter a valid name.")
        return name

    def clean_phone_number(self):
        phone_number = self.cleaned_data["phone_number"].strip()
        digits_only = "".join(ch for ch in phone_number if ch.isdigit())
        if len(digits_only) < 10:
            raise ValidationError("Enter a valid phone number.")
        return phone_number

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        existing_user = User.objects.filter(email__iexact=email).first()
        if existing_user:
            if existing_user.is_active:
                raise ValidationError("An account with this email already exists.")
            raise ValidationError(
                "This email is already registered but not verified. Use the resend verification email option below."
            )
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords do not match.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = generate_unique_username(self.cleaned_data["email"])
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()
        user.is_active = False
        if commit:
            user.save()
            Profile.objects.update_or_create(
                user=user,
                defaults={"phone_number": self.cleaned_data["phone_number"].strip()},
            )
        return user


class EmailOrUsernameAuthenticationForm(PremiumFormMixin, forms.Form):
    username = forms.CharField(label="Email or username")
    password = forms.CharField(widget=forms.PasswordInput, strip=False)

    error_messages = {
        "invalid_login": "Enter a valid email/username and password.",
        "inactive": "Your account is not active. Please verify your email first.",
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"placeholder": "Enter email or username", "autofocus": True})
        self.fields["password"].widget.attrs.update({"placeholder": "Enter password"})
        self.fields["username"].help_text = "You can sign in with either your username or email address."
        self.apply_premium_styles()

    def clean(self):
        cleaned_data = super().clean()
        identifier = cleaned_data.get("username", "").strip()
        password = cleaned_data.get("password")
        if not identifier or not password:
            if not identifier:
                self.add_error("username", "Enter your email address or username.")
            if not password:
                self.add_error("password", "Enter your password.")
            return cleaned_data

        user = authenticate(self.request, username=identifier, password=password)
        if user is None and "@" in identifier:
            matched_user = User.objects.filter(email__iexact=identifier).first()
            if matched_user:
                user = authenticate(self.request, username=matched_user.username, password=password)

        if user is None:
            raise ValidationError(self.error_messages["invalid_login"], code="invalid_login")
        if not user.is_active:
            raise ValidationError(self.error_messages["inactive"], code="inactive")

        self.user_cache = user
        return cleaned_data

    def get_user(self):
        return self.user_cache


class ProfileForm(PremiumFormMixin, forms.ModelForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=20, required=False)

    class Meta:
        model = Profile
        fields = ("profile_picture",)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["first_name"].initial = self.user.first_name
        self.fields["last_name"].initial = self.user.last_name
        self.fields["email"].initial = self.user.email
        self.fields["phone_number"].initial = self.instance.phone_number
        self.apply_premium_styles()

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise ValidationError("Another account already uses this email address.")
        return email

    def save(self, commit=True):
        profile = super().save(commit=False)
        self.user.first_name = self.cleaned_data["first_name"].strip()
        self.user.last_name = self.cleaned_data["last_name"].strip()
        self.user.email = self.cleaned_data["email"]
        profile.phone_number = self.cleaned_data["phone_number"].strip()
        if commit:
            self.user.save(update_fields=["first_name", "last_name", "email"])
            profile.save()
        return profile


class ResendVerificationForm(PremiumFormMixin, forms.Form):
    email = forms.EmailField(label="Email address")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update({"placeholder": "Enter your email"})
        self.fields["email"].help_text = "We will send a new verification link if this email belongs to an inactive account."
        self.apply_premium_styles()

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


class AddressForm(PremiumFormMixin, forms.ModelForm):
    class Meta:
        model = Address
        fields = (
            "full_name",
            "phone_number",
            "alternate_phone",
            "house_street",
            "landmark",
            "city",
            "state",
            "pincode",
            "country",
            "address_type",
            "latitude",
            "longitude",
            "is_default",
        )
        widgets = {
            "latitude": forms.HiddenInput(),
            "longitude": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["full_name"].widget.attrs.update({"placeholder": "Enter full name"})
        self.fields["phone_number"].widget.attrs.update({"placeholder": "10-digit mobile number"})
        self.fields["alternate_phone"].widget.attrs.update({"placeholder": "Alternate phone (optional)"})
        self.fields["alternate_phone"].required = False
        self.fields["house_street"].widget.attrs.update({"placeholder": "Flat no., Building, Street, Area"})
        self.fields["landmark"].widget.attrs.update({"placeholder": "E.g. Near City Mall (optional)"})
        self.fields["landmark"].required = False
        self.fields["city"].widget.attrs.update({"placeholder": "City / District", "id": "id_city"})
        self.fields["state"].widget.attrs.update({"placeholder": "State", "id": "id_state"})
        self.fields["pincode"].widget.attrs.update({
            "placeholder": "6-digit pincode",
            "id": "id_pincode",
            "maxlength": "6",
            "inputmode": "numeric",
        })
        self.fields["country"].widget.attrs.update({"placeholder": "Country", "id": "id_country"})
        self.fields["country"].initial = "India"
        self.fields["address_type"].widget = forms.HiddenInput()
        self.fields["address_type"].required = False
        # Remove premium styling from checkbox and hidden fields
        skip_premium = {"is_default", "address_type", "latitude", "longitude"}
        for name, field in self.fields.items():
            if name not in skip_premium:
                base_class = field.widget.attrs.get("class", "").strip()
                field.widget.attrs["class"] = f"{base_class} {self.input_class}".strip()

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number", "").strip()
        digits = "".join(ch for ch in phone if ch.isdigit())
        if len(digits) < 10:
            raise ValidationError("Enter a valid 10-digit mobile number.")
        return phone

    def clean_alternate_phone(self):
        phone = self.cleaned_data.get("alternate_phone", "").strip()
        if phone:
            digits = "".join(ch for ch in phone if ch.isdigit())
            if len(digits) < 10:
                raise ValidationError("Enter a valid 10-digit alternate number.")
        return phone

    def clean_pincode(self):
        pincode = self.cleaned_data.get("pincode", "").strip()
        if not pincode.isdigit() or len(pincode) != 6:
            raise ValidationError("Enter a valid 6-digit pincode.")
        return pincode

