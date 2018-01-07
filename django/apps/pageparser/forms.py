from django import forms
from django.core.validators import URLValidator


class URLField(forms.URLField):
    """
    Overloading default URLField to accept only http and https schemes
    """
    default_validators = [URLValidator(schemes=['http', 'https'])]


class URLSubmitForm(forms.Form):
    """
    A form for long URL with custom error messages and custom attributes for input field
    """
    target_url = URLField(
        label='',
        required=True,
        widget=forms.TextInput(
            attrs={
                'type': "text",
                'class': "text-center form-control form-control-lg",
                'placeholder': "Вставьте вашу ссылку",
            }
        ),
        error_messages={
            'invalid': 'Мы не уверены, что эта ссылка верна',
            'required': 'Обязательно нужна ссылка'
        }
    )
