from django import forms
from django.core.exceptions import ValidationError

from .fields import MosparoField

class MosparoForm(forms.Form):
    def clean(self):
        mosparo_field = None
        for key, field in self.fields.items():
            if isinstance(field, MosparoField):
                mosparo_field = field
                break

        if mosparo_field is None:
            raise ValidationError('No mosparo field found in form.')

        mosparo_field.verify_data(self)

        return super().clean()
