from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs.update({"class": css_class})


class UserRegistrationForm(BootstrapFormMixin, UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    role = forms.ChoiceField(choices=User.Role.choices, required=True)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "in_game_name",
            "password1",
            "password2",
        )

    def clean_email(self) -> str:
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email already in use.")
        return email


class UserProfileUpdateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "in_game_name",
            "discord_tag",
            "contact_number",
            "avatar",
        )

    def clean_email(self) -> str:
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Another account is already using this email address.")
        return email