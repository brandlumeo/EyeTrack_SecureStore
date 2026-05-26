from django import forms
from store.models import (
    Coupon, Category, Product, CameraSpecification,
    BiometricSpecification, SmartLockSpecification, NetworkDeviceSpecification,
    ServiceableArea,
)
from orders.models import DeliveryAgent, DeliveryAssignment, Technician
from support.models import FAQCategory, FAQ


# ─── Existing forms (unchanged) ───────────────────────────────────────────────

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            'code',
            'discount_percentage',
            'max_discount_amount',
            'valid_from',
            'valid_to',
            'max_uses',
            'active',
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control bg-transparent text-light border-secondary'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control bg-transparent text-light border-secondary', 'min': 1, 'max': 100}),
            'max_discount_amount': forms.NumberInput(attrs={'class': 'form-control bg-transparent text-light border-secondary', 'step': '0.01'}),
            'valid_from': forms.DateTimeInput(attrs={'class': 'form-control bg-transparent text-light border-secondary', 'type': 'datetime-local'}),
            'valid_to': forms.DateTimeInput(attrs={'class': 'form-control bg-transparent text-light border-secondary', 'type': 'datetime-local'}),
            'max_uses': forms.NumberInput(attrs={'class': 'form-control bg-transparent text-light border-secondary', 'min': 1}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Smart Cameras'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'bi-camera-video'}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'name', 'description', 'price', 'stock', 'image', 'is_available', 'installation_available', 'installation_charge', 'is_free_shipping']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'installation_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'installation_charge': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_free_shipping': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CameraSpecForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'camera_type', 'resolution', 'night_vision_range',
            'field_of_view', 'lens', 'frame_rate', 'weatherproof',
            'connectivity', 'power_source', 'storage_support',
            'audio_support', 'ai_detection', 'warranty'
        ]
        widgets = {
            'camera_type': forms.Select(attrs={'class': 'form-select bg-dark-soft text-light border-secondary'}),
            'resolution': forms.TextInput(attrs={'class': 'form-control bg-dark-soft text-light border-secondary'}),
            'night_vision_range': forms.TextInput(attrs={'class': 'form-control bg-dark-soft text-light border-secondary'}),
            'field_of_view': forms.TextInput(attrs={'class': 'form-control bg-dark-soft text-light border-secondary'}),
            'lens': forms.TextInput(attrs={'class': 'form-control bg-dark-soft text-light border-secondary'}),
            'frame_rate': forms.TextInput(attrs={'class': 'form-control bg-dark-soft text-light border-secondary'}),
            'weatherproof': forms.TextInput(attrs={'class': 'form-control bg-dark-soft text-light border-secondary'}),
            'connectivity': forms.Select(attrs={'class': 'form-select bg-dark-soft text-light border-secondary'}),
            'power_source': forms.Select(attrs={'class': 'form-select bg-dark-soft text-light border-secondary'}),
            'storage_support': forms.TextInput(attrs={'class': 'form-control bg-dark-soft text-light border-secondary'}),
            'audio_support': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ai_detection': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'warranty': forms.TextInput(attrs={'class': 'form-control bg-dark-soft text-light border-secondary'}),
        }


class BiometricSpecForm(forms.ModelForm):
    class Meta:
        model = BiometricSpecification
        exclude = ['product']
        widgets = {
            'authentication_method': forms.TextInput(attrs={'class': 'form-control bg-dark-soft text-light border-secondary'}),
            'user_capacity': forms.NumberInput(attrs={'class': 'form-control bg-dark-soft text-light border-secondary'}),
            'fingerprint_sensor': forms.TextInput(attrs={'class': 'form-control bg-dark-soft text-light border-secondary'}),
            'face_recognition': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'card_support': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'connectivity': forms.TextInput(attrs={'class': 'form-control bg-dark-soft text-light border-secondary'}),
            'power_supply': forms.TextInput(attrs={'class': 'form-control bg-dark-soft text-light border-secondary'}),
        }


class SmartLockSpecForm(forms.ModelForm):
    class Meta:
        model = SmartLockSpecification
        exclude = ['product']
        widgets = {
            'unlock_methods': forms.TextInput(attrs={'class': 'form-control bg-dark-soft text-light border-secondary'}),
            'connectivity': forms.TextInput(attrs={'class': 'form-control bg-dark-soft text-light border-secondary'}),
            'battery_life': forms.TextInput(attrs={'class': 'form-control bg-dark-soft text-light border-secondary'}),
            'emergency_unlock': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class NetworkSpecForm(forms.ModelForm):
    class Meta:
        model = NetworkDeviceSpecification
        exclude = ['product']
        widgets = {
            'ports': forms.NumberInput(attrs={'class': 'form-control bg-dark-soft text-light border-secondary'}),
            'bandwidth': forms.TextInput(attrs={'class': 'form-control bg-dark-soft text-light border-secondary'}),
            'poe_support': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class VideoDoorPhoneSpecForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'screen_size', 'camera_resolution', 'night_vision', 'connectivity_type',
            'unlock_method', 'audio_communication', 'mobile_app_support',
            'storage_support_vdp', 'power_source_vdp', 'installation_type', 'warranty_vdp'
        ]
        widgets = {
            'screen_size': forms.TextInput(attrs={'class': 'form-control bg-dark-soft text-light border-secondary'}),
            'camera_resolution': forms.TextInput(attrs={'class': 'form-control bg-dark-soft text-light border-secondary'}),
            'night_vision': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'connectivity_type': forms.Select(attrs={'class': 'form-select bg-dark-soft text-light border-secondary'}),
            'unlock_method': forms.Select(attrs={'class': 'form-select bg-dark-soft text-light border-secondary'}),
            'audio_communication': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mobile_app_support': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'storage_support_vdp': forms.TextInput(attrs={'class': 'form-control bg-dark-soft text-light border-secondary'}),
            'power_source_vdp': forms.Select(attrs={'class': 'form-select bg-dark-soft text-light border-secondary'}),
            'installation_type': forms.Select(attrs={'class': 'form-select bg-dark-soft text-light border-secondary'}),
            'warranty_vdp': forms.TextInput(attrs={'class': 'form-control bg-dark-soft text-light border-secondary'}),
        }


class DeliveryAgentForm(forms.ModelForm):
    """Form for adding/editing a delivery team member."""

    class Meta:
        model = DeliveryAgent
        fields = ['name', 'phone', 'vehicle_type', 'is_active', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control bg-transparent text-light border-secondary',
                'placeholder': 'Full name of agent',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control bg-transparent text-light border-secondary',
                'placeholder': '+91 9876543210',
            }),
            'vehicle_type': forms.Select(attrs={
                'class': 'form-select bg-transparent text-light border-secondary',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control bg-transparent text-light border-secondary',
                'rows': 3,
                'placeholder': 'Optional notes about this agent...',
            }),
        }


class AssignAgentForm(forms.ModelForm):
    """Form for assigning a delivery agent to an order."""

    class Meta:
        model = DeliveryAssignment
        fields = ['agent', 'estimated_delivery', 'delivery_notes']
        widgets = {
            'agent': forms.Select(attrs={
                'class': 'form-select bg-transparent text-light border-secondary',
            }),
            'estimated_delivery': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'class': 'form-control border-secondary',
                    'type': 'date',
                    'style': (
                        'background: rgba(255,255,255,0.08); '
                        'color: #f1f5f9; '
                        'color-scheme: dark;'
                    ),
                }
            ),
            'delivery_notes': forms.Textarea(attrs={
                'class': 'form-control bg-transparent text-light border-secondary',
                'rows': 2,
                'placeholder': 'Special delivery instructions...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active agents in the dropdown
        self.fields['agent'].queryset = DeliveryAgent.objects.filter(is_active=True)
        self.fields['agent'].empty_label = '— Select Agent —'


# ─── New Forms ────────────────────────────────────────────────────────────────

class ServiceableAreaForm(forms.ModelForm):
    """Form for managing delivery/installation coverage pincodes."""

    class Meta:
        model = ServiceableArea
        fields = [
            'pincode',
            'delivery_available',
            'installation_available',
            'delivery_charge',
            'estimated_delivery_days',
        ]
        widgets = {
            'pincode': forms.TextInput(attrs={
                'class': 'form-control bg-transparent text-light border-secondary',
                'placeholder': 'e.g. 673001',
                'maxlength': '6',
                'pattern': '[0-9]{6}',
            }),
            'estimated_delivery_days': forms.NumberInput(attrs={
                'class': 'form-control bg-transparent text-light border-secondary',
                'min': 1,
                'max': 30,
            }),
            'delivery_charge': forms.NumberInput(attrs={
                'class': 'form-control bg-transparent text-light border-secondary',
                'step': '0.01',
                'min': 0,
            }),
            'delivery_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'installation_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class FAQCategoryForm(forms.ModelForm):
    """Form for FAQ category management."""

    class Meta:
        model = FAQCategory
        fields = ['name', 'icon', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control bg-transparent text-light border-secondary',
                'placeholder': 'e.g. Installation & Setup',
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control bg-transparent text-light border-secondary',
                'placeholder': 'bi-tools',
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control bg-transparent text-light border-secondary',
                'min': 0,
            }),
        }


class FAQForm(forms.ModelForm):
    """Form for individual FAQ entry management."""

    class Meta:
        model = FAQ
        fields = ['category', 'question', 'answer', 'is_active', 'order']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-select bg-transparent text-light border-secondary',
            }),
            'question': forms.TextInput(attrs={
                'class': 'form-control bg-transparent text-light border-secondary',
                'placeholder': 'e.g. How long does installation take?',
            }),
            'answer': forms.Textarea(attrs={
                'class': 'form-control bg-transparent text-light border-secondary',
                'rows': 4,
                'placeholder': 'Provide a clear, helpful answer...',
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control bg-transparent text-light border-secondary',
                'min': 0,
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
class TechnicianForm(forms.ModelForm):
    """Form for adding/editing a verified technician profile."""

    class Meta:
        model = Technician
        fields = ['name', 'photo', 'phone', 'expertise_level', 'rating', 'is_verified', 'bio', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control bg-transparent text-light border-secondary',
                'placeholder': 'Professional Name',
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control bg-transparent text-light border-secondary',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control bg-transparent text-light border-secondary',
                'placeholder': '+91 9876543210',
            }),
            'expertise_level': forms.Select(attrs={
                'class': 'form-select bg-transparent text-light border-secondary',
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'form-control bg-transparent text-light border-secondary',
                'step': '0.1',
                'min': '0',
                'max': '5',
            }),
            'is_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'bio': forms.Textarea(attrs={
                'class': 'form-control bg-transparent text-light border-secondary',
                'rows': 3,
                'placeholder': 'Short professional bio for the customer tracking page...',
            }),
        }

from django.contrib.auth import get_user_model
User = get_user_model()

class UserForm(forms.ModelForm):
    """Form for adding/editing a user."""
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control bg-transparent text-light border-secondary'}), required=False, help_text="Leave empty to keep current password.")

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control bg-transparent text-light border-secondary'}),
            'email': forms.EmailInput(attrs={'class': 'form-control bg-transparent text-light border-secondary'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control bg-transparent text-light border-secondary'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control bg-transparent text-light border-secondary'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user
