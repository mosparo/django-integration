from django.forms import CharField, Form

from mosparo_django.fields import MosparoField
from mosparo_django.forms import MosparoForm


def test_mosparo_form():
    class DummyMosparoField(MosparoField):
        was_called = False

        def verify_data(self, form: Form):
            self.was_called = True

    class CustomForm(MosparoForm):
        name = CharField(label="Name", max_length=255)
        mosparo = DummyMosparoField()

    form = CustomForm({"name": "Test"})

    form.is_valid()

    assert form.fields["mosparo"].was_called is True


def test_mosparo_form_without_field():
    class CustomForm(MosparoForm):
        name = CharField(label="Name", max_length=255)

    form = CustomForm({"name": "Test"})

    res = form.is_valid()

    # Form should be invalid since no mosparo field was added to the form
    assert res is False


def test_plain_form_verifies_once():
    calls = []

    class DummyMosparoField(MosparoField):
        def verify_data(self, form: Form):
            calls.append(form)
            super().verify_data(form)

    class CustomForm(Form):
        name = CharField(label="Name", max_length=255)
        mosparo = DummyMosparoField()

        def clean(self):
            # The legacy manual verification must not hit the API again
            self.fields["mosparo"].verify_data(self)
            return super().clean()

    form = CustomForm({"name": "Test"})

    assert form.is_valid() is False
    assert calls == [form, form]
    assert form.errors == {
        "mosparo": ["mosparo specific fields were not found in the submitted data."],
        "__all__": ["mosparo specific fields were not found in the submitted data."],
    }
