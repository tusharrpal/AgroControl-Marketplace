from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    UserCreationForm,
)
from django.core.validators import RegexValidator

from marketplace.models import Product

from .models import User


class BootstrapFormMixin:
    """Apply consistent Bootstrap styling without repeating widget definitions."""

    def apply_bootstrap_classes(self):
        for field in self.fields.values():
            css_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs["class"] = css_class
            if not isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("placeholder", field.label)


class RegistrationForm(BootstrapFormMixin, UserCreationForm):
    phone_validator = RegexValidator(
        regex=r"^\+?[0-9]{10,15}$",
        message="Enter a valid phone number containing 10 to 15 digits.",
    )
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, validators=[phone_validator])

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "phone_number",
            "password1",
            "password2",
        )

    def __init__(self, *args, role, **kwargs):
        self.role = role
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()
        self.order_fields(self.Meta.fields)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.role
        if commit:
            user.save()
        return user


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()


class ProfileForm(BootstrapFormMixin, forms.ModelForm):
    phone_validator = RegexValidator(
        regex=r"^\+?[0-9]{10,15}$",
        message="Enter a valid phone number containing 10 to 15 digits.",
    )
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, validators=[phone_validator])

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "phone_number",
            "profile_photo",
        )
        widgets = {
            "profile_photo": forms.FileInput(attrs={"accept": "image/*"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        duplicate = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class ProfilePasswordChangeForm(BootstrapFormMixin, PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()


class CropForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            "name",
            "category",
            "description",
            "price",
            "quantity",
            "unit",
            "location",
            "harvest_date",
            "is_organic",
            "is_available",
            "image",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "harvest_date": forms.DateInput(attrs={"type": "date"}),
            "image": forms.FileInput(attrs={"accept": "image/*"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()
        for field_name in ("is_organic", "is_available"):
            self.fields[field_name].widget.attrs["class"] = "form-check-input"

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price <= 0:
            raise forms.ValidationError("Price must be greater than zero.")
        return price
