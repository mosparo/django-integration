from django import forms
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError

from mosparo import Client
from mosparo_django.config import FrontendConfig
from mosparo_django.widgets import MosparoWidget


class MosparoField(forms.BooleanField):
    widget = MosparoWidget

    mosparo_host = None
    mosparo_uuid = None
    mosparo_public_key = None
    mosparo_private_key = None
    mosparo_verify_ssl = True

    def __init__(self, mosparo_host=None, mosparo_uuid=None, mosparo_public_key=None, mosparo_private_key=None,
                 mosparo_verify_ssl=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not isinstance(self.widget, MosparoWidget):
            raise ImproperlyConfigured(
                "The widget must be a subclass of mosparo_django.widgets.MosparoWidget"
            )

        if mosparo_host is None:
            mosparo_host = getattr(settings, 'MOSPARO_HOST', '')

        if mosparo_uuid is None or mosparo_public_key is None or mosparo_private_key is None:
            mosparo_uuid = getattr(settings, 'MOSPARO_UUID', '')
            mosparo_public_key = getattr(settings, 'MOSPARO_PUBLIC_KEY', '')
            mosparo_private_key = getattr(settings, 'MOSPARO_PRIVATE_KEY', '')

        if mosparo_verify_ssl is None:
            mosparo_verify_ssl = getattr(settings, 'MOSPARO_VERIFY_SSL', True)

        self.mosparo_host = mosparo_host
        self.mosparo_uuid = mosparo_uuid
        self.mosparo_public_key = mosparo_public_key
        self.mosparo_private_key = mosparo_private_key
        self.mosparo_verify_ssl = mosparo_verify_ssl

        frontend_config = FrontendConfig(self.mosparo_host, self.mosparo_uuid, self.mosparo_public_key)
        self.widget.set_frontend_config(frontend_config)

    def validate(self, value):
        return True

    def verify_data(self, form: forms.Form):
        api_client = Client(
            self.mosparo_host,
            self.mosparo_public_key,
            self.mosparo_private_key,
            self.mosparo_verify_ssl
        )

        if '_mosparo_submitToken' not in form.data or '_mosparo_validationToken' not in form.data:
            raise ValidationError('mosparo specific fields were not found in the submitted data.')

        submit_token = form.data['_mosparo_submitToken']
        validation_token = form.data['_mosparo_validationToken']

        res = api_client.verify_submission(form.data.dict(), submit_token, validation_token)

        if not res.is_submittable():
            form.valid = False
            raise ValidationError('mosparo could not verify the data. Please check the submission in mosparo.')

    def get_mosparo_host(self):
        return self.mosparo_host

    def get_mosparo_uuid(self):
        return self.mosparo_uuid

    def get_mosparo_public_key(self):
        return self.mosparo_public_key
