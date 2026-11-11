import re

from django import forms

from .models import QuoteRequest, ServiceTicket


class QuoteRequestForm(forms.ModelForm):
    # Honeypot: real users never see or fill this field.
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = QuoteRequest
        fields = ["name", "phone", "email", "site_type", "camera_count", "pincode", "location", "message", "package"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 3}),
            "package": forms.HiddenInput,
        }

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        digits = re.sub(r"\D", "", phone)
        if len(digits) < 10 or len(digits) > 13:
            raise forms.ValidationError("Enter a valid 10-digit mobile number.")
        return phone

    def clean_pincode(self):
        pincode = self.cleaned_data.get("pincode", "").strip()
        if pincode and not re.fullmatch(r"\d{6}", pincode):
            raise forms.ValidationError("Enter a valid 6-digit pincode.")
        return pincode


class ServiceTicketForm(forms.ModelForm):
    class Meta:
        model = ServiceTicket
        fields = ["order", "category", "subject", "description", "contact_phone", "site_location"]
        widgets = {
            "order": forms.Select(attrs={"class": "form-select premium-input"}),
            "category": forms.Select(attrs={"class": "form-select premium-input"}),
            "subject": forms.TextInput(attrs={"class": "form-control premium-input", "maxlength": 150,
                                              "placeholder": "e.g. Gate camera shows no video since yesterday"}),
            "description": forms.Textarea(attrs={"class": "form-control premium-input", "rows": 5,
                                                 "placeholder": "What happened, which camera or device, since when, anything you already tried..."}),
            "contact_phone": forms.TextInput(attrs={"class": "form-control premium-input", "inputmode": "tel"}),
            "site_location": forms.TextInput(attrs={"class": "form-control premium-input", "placeholder": "e.g. Perambra, Kozhikode"}),
        }
        labels = {"order": "Related order (optional)", "contact_phone": "Phone number for the technician",
                  "site_location": "Where is the equipment installed?"}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        from orders.models import Order
        orders = Order.objects.filter(user=user).order_by("-created_at") if user else Order.objects.none()
        self.fields["order"].queryset = orders
        self.fields["order"].required = False
        self.fields["order"].empty_label = "Not related to a specific order"
        self.fields["order"].label_from_instance = lambda o: "%s - %s (%s)" % (o.formatted_id, o.created_at.strftime("%d %b %Y"), o.get_order_status_display())

    def clean_contact_phone(self):
        phone = self.cleaned_data["contact_phone"].strip()
        if not 10 <= len(re.sub(r"\D", "", phone)) <= 13:
            raise forms.ValidationError("Enter a valid 10-digit mobile number.")
        return phone


class TicketReplyForm(forms.Form):
    body = forms.CharField(widget=forms.Textarea(attrs={"class": "form-control premium-input", "rows": 3,
                                                        "placeholder": "Write a reply..."}), max_length=5000)
