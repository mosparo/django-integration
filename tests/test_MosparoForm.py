from django.forms import Form, CharField

from mosparo_django.forms import MosparoForm
from mosparo_django.fields import MosparoField

def test_mosparo_form():
    class DummyMosparoField(MosparoField):
        was_called = False

        def verify_data(self, form: Form):
            self.was_called = True

    class CustomForm(MosparoForm):
        name = CharField(label='Name', max_length=255)
        mosparo = DummyMosparoField()

    form = CustomForm({
        'name': 'Test'
    })

    form.is_valid()

    assert form.fields['mosparo'].was_called is True

def test_mosparo_form_without_field():
    class CustomForm(MosparoForm):
        name = CharField(label='Name', max_length=255)

    form = CustomForm({
        'name': 'Test'
    })

    res = form.is_valid()

    # Form should be invalid since no mosparo field was added to the form
    assert res is False
