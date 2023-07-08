from django import forms
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError

from mosparo_api_client import Client
from mosparo_django.config import FrontendConfig
from mosparo_django.widgets import MosparoWidget


class MosparoField(forms.BooleanField):
    widget = MosparoWidget

    mosparo_host = None
    mosparo_uuid = None
    mosparo_public_key = None
    mosparo_private_key = None
    mosparo_verify_ssl = True

    callback_ignored_field_types = None
    callback_verifiable_field_types = None
    callback_after_prepare_form_data = None

    def __init__(self, mosparo_host=None, mosparo_uuid=None, mosparo_public_key=None, mosparo_private_key=None,
                 mosparo_verify_ssl=None, callback_ignored_field_types=None, callback_verifiable_field_types=None,
                 callback_after_prepare_form_data=None, *args, **kwargs):
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

        self.callback_ignored_field_types = callback_ignored_field_types
        self.callback_verifiable_field_types = callback_verifiable_field_types
        self.callback_after_prepare_form_data = callback_after_prepare_form_data

        frontend_config = FrontendConfig(self.mosparo_host, self.mosparo_uuid, self.mosparo_public_key)
        self.widget.set_frontend_config(frontend_config)

        # Hide the label for the field, important for the invisible mode.
        self.label = ''

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

        data = self.prepare_form_data(form)
        submit_token = form.data['_mosparo_submitToken']
        validation_token = form.data['_mosparo_validationToken']

        res = api_client.verify_submission(data['form_data'], submit_token, validation_token)

        if res != None:
            verified_fields = res.get_verified_fields()
            required_field_difference = set(data['required_fields']) - set(verified_fields.keys())
            verifiable_field_difference = set(data['verifiable_fields']) - set(verified_fields.keys())

            # The submission is only valid if all required and verifiable fields got verified
            if res.is_submittable() and not required_field_difference and not verifiable_field_difference:
                form.valid = True
                return

        form.valid = False
        raise ValidationError('mosparo could not verify the data. Please check the submission in mosparo.')

    def get_mosparo_host(self):
        return self.mosparo_host

    def get_mosparo_uuid(self):
        return self.mosparo_uuid

    def get_mosparo_public_key(self):
        return self.mosparo_public_key

    def prepare_form_data(self, form: forms.Form):
        data = { 'form_data': {}, 'required_fields': [], 'verifiable_fields': [] }
        ignored_field_types = [
            'PasswordInput',
            'HiddenInput',
            'MultipleHiddenInput',
            'FileInput',
            'ClearableFileInput',
            'MosparoField',
        ]
        if self.callback_ignored_field_types != None:
            ignored_field_types = self.callback_ignored_field_types(ignored_field_types)
        
        verifiable_field_types = [
            'TextInput',
            'Textarea',
            'EmailInput',
            'URLInput',
        ]
        if self.callback_verifiable_field_types != None:
            verifiable_field_types = self.callback_verifiable_field_types(verifiable_field_types)

        for key, field in form.fields.items():
            if type(field).__name__ in ignored_field_types or type(field.widget).__name__ in ignored_field_types:
                continue

            name = key

            if field.required:
                data['required_fields'].append(name)

            if type(field).__name__ in verifiable_field_types or type(field.widget).__name__ in verifiable_field_types:
                data['verifiable_fields'].append(name)

            if key in form.data:
                data['form_data'][key] = form.data[key]

        if self.callback_after_prepare_form_data != None:
            data = self.callback_after_prepare_form_data(data)

        return data