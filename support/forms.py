import re

from django import forms

from .models import QuoteRequest


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
