from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .fields import MosparoField


class MosparoForm(forms.Form):
    # MosparoField verifies the submission itself, a plain forms.Form works
    # just as well. This class only ensures that the field isn't forgotten.
    def clean(self):
        if not any(isinstance(f, MosparoField) for f in self.fields.values()):
            raise ValidationError(_("No mosparo field found in form."))

        return super().clean()
