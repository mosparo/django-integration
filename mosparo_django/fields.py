from django import forms
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError

from mosparo import Client
from mosparo_django.widgets import MosparoWidget

class MosparoField(forms.BooleanField):
    widget = MosparoWidget

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not isinstance(self.widget, MosparoWidget):
            raise ImproperlyConfigured(
                "The widget must be a subclass of mosparo_django.widgets.MosparoWidget"
            )

    def validate(self, value):
        return True

    def verify_data(self, form: forms.Form):
        api_client = Client(
            getattr(settings, 'MOSPARO_HOST', ''),
            getattr(settings, 'MOSPARO_PUBLIC_KEY', ''),
            getattr(settings, 'MOSPARO_PRIVATE_KEY', ''),
            getattr(settings, 'MOSPARO_VERIFY_SSL', True)
        )

        if '_mosparo_submitToken' not in form.data or '_mosparo_validationToken' not in form.data:
            raise ValidationError('mosparo specific fields were not found in the submitted data.')

        submit_token = form.data['_mosparo_submitToken']
        validation_token = form.data['_mosparo_validationToken']

        res = api_client.verify_submission(form.cleaned_data, submit_token, validation_token)

        if not res.is_submittable():
            raise ValidationError('mosparo could not verify the data. Please check the submission in mosparo.')
