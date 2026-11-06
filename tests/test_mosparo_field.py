import pytest
import requests
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.forms import (
    BooleanField,
    CharField,
    CheckboxSelectMultiple,
    ChoiceField,
    DateField,
    FileField,
    Form,
    HiddenInput,
    ImageField,
    MultipleChoiceField,
    MultipleHiddenInput,
    NullBooleanField,
    PasswordInput,
    RadioSelect,
    Select,
    SelectDateWidget,
    SplitDateTimeField,
    SplitDateTimeWidget,
    SplitHiddenDateTimeWidget,
    Textarea,
    TextInput,
    URLField,
    Widget,
)
from django.forms.widgets import Input
from django.http import QueryDict
from mosparo_api_client import RequestHelper, VerificationResult

from mosparo_django.fields import MosparoField


def test_mosparo_field():
    mf = MosparoField()

    assert "https://host.local" == mf.get_mosparo_host()
    assert "uuid" == mf.get_mosparo_uuid()
    assert "public_key" == mf.get_mosparo_public_key()
    assert mf.validate(1) is True


def test_mosparo_field_custom_args():
    mf = MosparoField(
        mosparo_host="https://custom-test.local",
        mosparo_uuid="custom_uuid",
        mosparo_public_key="custom_public_key",
        mosparo_private_key="custom_private_key",
    )

    assert "https://custom-test.local" == mf.get_mosparo_host()
    assert "custom_uuid" == mf.get_mosparo_uuid()
    assert "custom_public_key" == mf.get_mosparo_public_key()
    assert mf.validate(1) is True

    assert "https://custom-test.local" == mf.widget.frontend_config.get_host()
    assert "custom_uuid" == mf.widget.frontend_config.get_uuid()
    assert "custom_public_key" == mf.widget.frontend_config.get_public_key()


def test_mosparo_field_custom_widget():
    class CustomMosparoField(MosparoField):
        widget = Widget

    with pytest.raises(ImproperlyConfigured) as exc:
        CustomMosparoField()

    assert (
        "The widget must be a subclass of mosparo_django.widgets.MosparoWidget"
        in str(exc.value)
    )


def test_mosparo_field_verify_data_without_mosparo_tokens():
    class DummyForm(Form):
        data = {"name": "Test"}

    form = DummyForm()
    mf = MosparoField()

    with pytest.raises(ValidationError) as exc:
        mf.verify_data(form)

    assert "mosparo specific fields were not found in the submitted data." in str(
        exc.value
    )


def test_mosparo_field_verify_data(requests_mock):
    # Prepare the form
    class DummyForm(Form):
        name = CharField(label="Name", max_length=255)
        password = CharField(label="Password", max_length=255, widget=PasswordInput)

    data = QueryDict(
        "name=Test&_mosparo_submitToken=submitToken&_mosparo_validationToken=validationToken"
    )
    form = DummyForm(data=data)

    form.is_valid()

    # Prepare the API request
    public_key = "public_key"
    private_key = "private_key"
    validation_token = "validationToken"
    form_data = {"name": "Test"}

    request_helper = RequestHelper(public_key, private_key)

    prepared_form_data = request_helper.prepare_form_data(form_data)
    form_signature = request_helper.create_form_data_hmac_hash(prepared_form_data)

    validation_signature = request_helper.create_hmac_hash(validation_token)
    verification_signature = request_helper.create_hmac_hash(
        validation_signature + form_signature
    )

    requests_mock.post(
        "https://host.local/api/v1/verification/verify",
        json={
            "valid": True,
            "verificationSignature": verification_signature,
            "verifiedFields": {"name": VerificationResult.FIELD_VALID},
            "issues": [],
        },
        status_code=200,
    )

    mf = MosparoField()
    mf.verify_data(form)


def test_mosparo_field_verify_data_with_ignored_field(requests_mock):
    # Prepare the form
    class DummyForm(Form):
        name = CharField(label="Name", max_length=255)
        email = CharField(
            label="Email",
            max_length=255,
            widget=TextInput(attrs={"class": "mosparo__ignored-field"}),
        )
        password = CharField(label="Password", max_length=255, widget=PasswordInput)

    data = QueryDict(
        "name=Test&email=test@example.com&_mosparo_submitToken=submitToken&_mosparo_validationToken=validationToken"
    )
    form = DummyForm(data=data)

    form.is_valid()

    # Prepare the API request
    public_key = "public_key"
    private_key = "private_key"
    validation_token = "validationToken"
    form_data = {"name": "Test"}

    request_helper = RequestHelper(public_key, private_key)

    prepared_form_data = request_helper.prepare_form_data(form_data)
    form_signature = request_helper.create_form_data_hmac_hash(prepared_form_data)

    validation_signature = request_helper.create_hmac_hash(validation_token)
    verification_signature = request_helper.create_hmac_hash(
        validation_signature + form_signature
    )

    requests_mock.post(
        "https://host.local/api/v1/verification/verify",
        json={
            "valid": True,
            "verificationSignature": verification_signature,
            "verifiedFields": {"name": VerificationResult.FIELD_VALID},
            "issues": [],
        },
        status_code=200,
    )

    mf = MosparoField()
    mf.verify_data(form)


def test_mosparo_field_verify_data_with_verifiable_callback(requests_mock):
    class TestInput(Input):
        input_type = "text"

    # Prepare the form
    class DummyForm(Form):
        name = CharField(label="Name", max_length=255)
        url = URLField(label="URL", max_length=255, required=False)
        test_field = CharField(
            label="Test", max_length=255, required=False, widget=TestInput
        )

    data = QueryDict(
        "name=Test&_mosparo_submitToken=submitToken&_mosparo_validationToken=validationToken"
    )
    form = DummyForm(data=data)

    form.is_valid()

    # Prepare the API request
    public_key = "public_key"
    private_key = "private_key"
    validation_token = "validationToken"
    form_data = {"name": "Test"}

    request_helper = RequestHelper(public_key, private_key)

    prepared_form_data = request_helper.prepare_form_data(form_data)
    form_signature = request_helper.create_form_data_hmac_hash(prepared_form_data)

    validation_signature = request_helper.create_hmac_hash(validation_token)
    verification_signature = request_helper.create_hmac_hash(
        validation_signature + form_signature
    )

    requests_mock.post(
        "https://host.local/api/v1/verification/verify",
        json={
            "valid": True,
            "verificationSignature": verification_signature,
            "verifiedFields": {
                "name": VerificationResult.FIELD_VALID,
                "url": VerificationResult.FIELD_VALID,
            },
            "issues": [],
        },
        status_code=200,
    )

    def test_callback(types):
        # Add TestInput to the list of verifiable fields
        return types + [TestInput]

    mf = MosparoField(callback_verifiable_field_types=test_callback)

    with pytest.raises(ValidationError) as exc:
        mf.verify_data(form)

    # Fails, because not all verifiable fields got verified (the TestInput field type was missing)
    assert "The spam protection could not verify the data." in str(exc.value)


def test_mosparo_field_ignores_subclasses_of_ignored_types():
    class CustomPasswordInput(PasswordInput):
        pass

    class DummyForm(Form):
        name = CharField(label="Name", max_length=255)
        password = CharField(
            label="Password", max_length=255, widget=CustomPasswordInput
        )
        mosparo = MosparoField()

    form = DummyForm(data=QueryDict("name=Test&password=secret"))

    assert form.fields["mosparo"].prepare_form_data(form) == {
        "form_data": {"name": "Test"},
        "required_fields": ["name"],
        "verifiable_fields": ["name"],
    }


def test_mosparo_field_rejects_field_type_names():
    class DummyForm(Form):
        name = CharField(label="Name", max_length=255)

    form = DummyForm(data=QueryDict("name=Test"))
    mf = MosparoField(
        callback_verifiable_field_types=lambda types: types + ["TestInput"],
    )

    with pytest.raises(ImproperlyConfigured) as exc:
        mf.prepare_form_data(form)

    assert "'TestInput'" in str(exc.value)


def test_mosparo_field_ignores_fields_by_html_type():
    choices = [("a", "A"), ("b", "B")]

    class DummyForm(Form):
        name = CharField(label="Name", max_length=255)
        password = CharField(widget=PasswordInput)
        hidden = CharField(widget=HiddenInput)
        multiple_hidden = MultipleChoiceField(
            choices=choices, widget=MultipleHiddenInput
        )
        file = FileField()
        image = ImageField(required=False)
        accept = BooleanField()
        radio = ChoiceField(choices=choices, widget=RadioSelect)
        checkboxes = MultipleChoiceField(choices=choices, widget=CheckboxSelectMultiple)
        mosparo = MosparoField()

    form = DummyForm(
        data=QueryDict(
            "name=Test&password=secret&hidden=x&multiple_hidden=a&accept=on"
            "&radio=a&checkboxes=a&checkboxes=b"
        )
    )

    assert form.fields["mosparo"].prepare_form_data(form) == {
        "form_data": {"name": "Test"},
        "required_fields": ["name"],
        "verifiable_fields": ["name"],
    }


def test_mosparo_field_collects_select_based_fields():
    # The frontend collects <select>, so these must be sent to mosparo as well,
    # even though they are BooleanField (sub)classes.
    class CustomBooleanField(BooleanField):
        pass

    class DummyForm(Form):
        newsletter = NullBooleanField()
        agree = BooleanField(widget=Select(choices=[("True", "Yes"), ("", "No")]))
        custom = CustomBooleanField(
            required=False, widget=Select(choices=[("True", "Yes"), ("", "No")])
        )
        country = ChoiceField(choices=[("ch", "Switzerland")])
        birthday = DateField(required=False)
        message = CharField(widget=Textarea)
        mosparo = MosparoField()

    form = DummyForm(
        data=QueryDict(
            "newsletter=true&agree=True&custom=&country=ch&birthday=2000-01-01"
            "&message=Hello"
        )
    )

    assert form.fields["mosparo"].prepare_form_data(form) == {
        "form_data": {
            "newsletter": "true",
            "agree": "True",
            "custom": "",
            "country": "ch",
            "birthday": "2000-01-01",
            "message": "Hello",
        },
        "required_fields": ["newsletter", "agree", "country", "message"],
        # DateInput is a TextInput and renders type="text"
        "verifiable_fields": ["birthday", "message"],
    }


def test_mosparo_field_ignored_field_class():
    class DummyForm(Form):
        name = CharField(label="Name", max_length=255)
        ignored = CharField(
            widget=TextInput(attrs={"class": "form-control mosparo__ignored-field"})
        )
        # Only the exact class name ignores a field
        similar = CharField(
            widget=TextInput(attrs={"class": "mosparo__ignored-field-not"})
        )
        mosparo = MosparoField()

    form = DummyForm(data=QueryDict("name=Test&ignored=x&similar=y"))

    assert form.fields["mosparo"].prepare_form_data(form) == {
        "form_data": {"name": "Test", "similar": "y"},
        "required_fields": ["name", "similar"],
        "verifiable_fields": ["name", "similar"],
    }


def test_mosparo_field_verify_data_with_after_data_callback(requests_mock):
    class TestInput(TextInput):
        pass

    # Prepare the form
    class DummyForm(Form):
        name = CharField(label="Name", max_length=255)
        url = URLField(label="URL", max_length=255, required=False)
        test_field = CharField(
            label="Test", max_length=255, required=False, widget=TestInput
        )

    data = QueryDict(
        "name=Test&_mosparo_submitToken=submitToken&_mosparo_validationToken=validationToken"
    )
    form = DummyForm(data=data)

    form.is_valid()

    # Prepare the API request
    public_key = "public_key"
    private_key = "private_key"
    validation_token = "validationToken"
    form_data = {"name": "Test"}

    request_helper = RequestHelper(public_key, private_key)

    prepared_form_data = request_helper.prepare_form_data(form_data)
    form_signature = request_helper.create_form_data_hmac_hash(prepared_form_data)

    validation_signature = request_helper.create_hmac_hash(validation_token)
    verification_signature = request_helper.create_hmac_hash(
        validation_signature + form_signature
    )

    requests_mock.post(
        "https://host.local/api/v1/verification/verify",
        json={
            "valid": True,
            "verificationSignature": verification_signature,
            "verifiedFields": {
                "name": VerificationResult.FIELD_VALID,
                "url": VerificationResult.FIELD_VALID,
            },
            "issues": [],
        },
        status_code=200,
    )

    def test_callback(data):
        data["required_fields"].append("test-field")
        return data

    mf = MosparoField(callback_after_prepare_form_data=test_callback)

    with pytest.raises(ValidationError) as exc:
        mf.verify_data(form)

    assert "The spam protection could not verify the data." in str(exc.value)


def test_mosparo_field_verify_data_validation_error(requests_mock):
    # Prepare the form
    class DummyForm(Form):
        name = CharField(label="Name", max_length=255)

    data = QueryDict(
        "name=Test&_mosparo_submitToken=submitToken&_mosparo_validationToken=validationToken"
    )
    form = DummyForm(data=data)

    form.is_valid()

    # Prepare the API request
    public_key = "public_key"
    private_key = "private_key"
    validation_token = "validationToken"
    form_data = {"name": "Test"}

    request_helper = RequestHelper(public_key, private_key)

    prepared_form_data = request_helper.prepare_form_data(form_data)
    form_signature = request_helper.create_form_data_hmac_hash(prepared_form_data)

    validation_signature = request_helper.create_hmac_hash(validation_token)
    verification_signature = request_helper.create_hmac_hash(
        validation_signature + form_signature
    )

    requests_mock.post(
        "https://host.local/api/v1/verification/verify",
        json={
            "valid": False,
            "verificationSignature": verification_signature,
            "verifiedFields": {"name": VerificationResult.FIELD_VALID},
            "issues": [],
        },
        status_code=200,
    )

    mf = MosparoField()

    with pytest.raises(ValidationError) as exc:
        mf.verify_data(form)

    assert "The spam protection could not verify the data." in str(exc.value)


def test_mosparo_field_clean_outside_of_form():
    mf = MosparoField()

    with pytest.raises(ImproperlyConfigured):
        mf.clean(None)


def test_mosparo_field_in_plain_form(requests_mock):
    class DummyForm(Form):
        name = CharField(label="Name", max_length=255)
        mosparo = MosparoField()

    request_helper = RequestHelper("public_key", "private_key")
    prepared_form_data = request_helper.prepare_form_data({"name": "Test"})
    form_signature = request_helper.create_form_data_hmac_hash(prepared_form_data)
    validation_signature = request_helper.create_hmac_hash("validationToken")
    verification_signature = request_helper.create_hmac_hash(
        validation_signature + form_signature
    )

    requests_mock.post(
        "https://host.local/api/v1/verification/verify",
        json={
            "valid": True,
            "verificationSignature": verification_signature,
            "verifiedFields": {"name": VerificationResult.FIELD_VALID},
            "issues": [],
        },
        status_code=200,
    )

    form = DummyForm(
        data=QueryDict(
            "name=Test&_mosparo_submitToken=submitToken&_mosparo_validationToken=validationToken"
        )
    )

    assert form.is_valid() is True
    assert requests_mock.call_count == 1

    # Verifying the same form again doesn't hit the API
    form.fields["mosparo"].verify_data(form)
    assert requests_mock.call_count == 1


def test_mosparo_field_in_prefixed_form(requests_mock):
    class DummyForm(Form):
        name = CharField(label="Name", max_length=255)
        mosparo = MosparoField()

    request_helper = RequestHelper("public_key", "private_key")
    prepared_form_data = request_helper.prepare_form_data({"contact-name": "Test"})
    form_signature = request_helper.create_form_data_hmac_hash(prepared_form_data)
    validation_signature = request_helper.create_hmac_hash("validationToken")
    verification_signature = request_helper.create_hmac_hash(
        validation_signature + form_signature
    )

    requests_mock.post(
        "https://host.local/api/v1/verification/verify",
        json={
            "valid": True,
            "verificationSignature": verification_signature,
            "verifiedFields": {"contact-name": VerificationResult.FIELD_VALID},
            "issues": [],
        },
        status_code=200,
    )

    # The mosparo tokens are added by the frontend and are never prefixed
    form = DummyForm(
        data=QueryDict(
            "contact-name=Test&_mosparo_submitToken=submitToken&_mosparo_validationToken=validationToken"
        ),
        prefix="contact",
    )

    assert form.fields["mosparo"].prepare_form_data(form) == {
        "form_data": {"contact-name": "Test"},
        "required_fields": ["contact-name"],
        "verifiable_fields": ["contact-name"],
    }
    assert form.is_valid() is True


def test_mosparo_field_repeated_full_clean_keeps_error():
    class DummyForm(Form):
        name = CharField(label="Name", max_length=255)
        mosparo = MosparoField()

    form = DummyForm({"name": "Test"})

    assert form.is_valid() is False
    form.full_clean()
    assert form.is_valid() is False
    assert "mosparo" in form.errors


def test_mosparo_field_retries_after_connection_error(requests_mock, caplog):
    class DummyForm(Form):
        name = CharField(label="Name", max_length=255)
        mosparo = MosparoField()

    request_helper = RequestHelper("public_key", "private_key")
    prepared_form_data = request_helper.prepare_form_data({"name": "Test"})
    form_signature = request_helper.create_form_data_hmac_hash(prepared_form_data)
    validation_signature = request_helper.create_hmac_hash("validationToken")
    verification_signature = request_helper.create_hmac_hash(
        validation_signature + form_signature
    )

    form = DummyForm(
        data=QueryDict(
            "name=Test&_mosparo_submitToken=submitToken&_mosparo_validationToken=validationToken"
        )
    )

    # mosparo is not reachable, the error must not be cached as a result
    requests_mock.post(
        "https://host.local/api/v1/verification/verify",
        exc=requests.exceptions.ConnectTimeout,
    )
    form.full_clean()

    assert form.is_valid() is False
    assert form.errors == {
        "mosparo": [
            "The spam protection is currently unavailable. Please try again later."
        ]
    }
    assert "The submission could not be verified with mosparo." in caplog.text

    # mosparo is reachable again, the submission gets verified
    requests_mock.post(
        "https://host.local/api/v1/verification/verify",
        json={
            "valid": True,
            "verificationSignature": verification_signature,
            "verifiedFields": {"name": VerificationResult.FIELD_VALID},
            "issues": [],
        },
        status_code=200,
    )
    form.full_clean()

    assert form.is_valid() is True
    assert requests_mock.call_count == 2


@pytest.mark.parametrize(
    "setting, argument, expected",
    [
        (Ellipsis, None, 10),
        (3, None, 3),
        (None, None, None),
        (3, 5, 5),
        (3, (2, 7), (2, 7)),
    ],
)
def test_mosparo_field_timeout(requests_mock, settings, setting, argument, expected):
    if setting is not Ellipsis:
        settings.MOSPARO_TIMEOUT = setting

    class DummyForm(Form):
        name = CharField(label="Name", max_length=255)
        mosparo = MosparoField(mosparo_timeout=argument)

    requests_mock.post(
        "https://host.local/api/v1/verification/verify",
        json={"valid": False},
        status_code=200,
    )

    form = DummyForm(
        data=QueryDict(
            "name=Test&_mosparo_submitToken=submitToken&_mosparo_validationToken=validationToken"
        )
    )
    form.is_valid()

    assert requests_mock.last_request.timeout == expected


def test_mosparo_field_timeout_error(requests_mock):
    class DummyForm(Form):
        name = CharField(label="Name", max_length=255)
        mosparo = MosparoField()

    requests_mock.post(
        "https://host.local/api/v1/verification/verify",
        exc=requests.exceptions.ReadTimeout,
    )

    form = DummyForm(
        data=QueryDict(
            "name=Test&_mosparo_submitToken=submitToken&_mosparo_validationToken=validationToken"
        )
    )

    assert form.is_valid() is False
    assert form.errors == {
        "mosparo": [
            "The spam protection is currently unavailable. Please try again later."
        ]
    }


def test_mosparo_field_invalid_response(requests_mock):
    class DummyForm(Form):
        name = CharField(label="Name", max_length=255)
        mosparo = MosparoField()

    # For example, a proxy in front of mosparo returns an HTML error page
    requests_mock.post(
        "https://host.local/api/v1/verification/verify",
        text="<html>502 Bad Gateway</html>",
        status_code=502,
    )

    form = DummyForm(
        data=QueryDict(
            "name=Test&_mosparo_submitToken=submitToken&_mosparo_validationToken=validationToken"
        )
    )

    assert form.is_valid() is False
    assert form.errors == {
        "mosparo": [
            "The spam protection is currently unavailable. Please try again later."
        ]
    }


@pytest.mark.parametrize("prefix", [None, "contact"])
def test_mosparo_field_prepare_form_data_with_multiple_inputs(prefix):
    # Widgets which render several inputs are sent input by input, like the
    # frontend collects them.
    class DummyForm(Form):
        appointment = SplitDateTimeField()
        hidden_appointment = SplitDateTimeField(widget=SplitHiddenDateTimeWidget)
        ignored_appointment = SplitDateTimeField(
            widget=SplitDateTimeWidget(attrs={"class": "mosparo__ignored-field"})
        )
        birthday = DateField(widget=SelectDateWidget(years=[2000]), required=False)
        mosparo = MosparoField()

    def name(key):
        return f"{prefix}-{key}" if prefix else key

    data = QueryDict(mutable=True)
    data.update(
        {
            name("appointment_0"): "2026-11-03",
            name("appointment_1"): "10:00",
            name("hidden_appointment_0"): "2026-11-03",
            name("hidden_appointment_1"): "11:00",
            name("ignored_appointment_0"): "2026-11-03",
            name("ignored_appointment_1"): "12:00",
            name("birthday_year"): "2000",
            name("birthday_month"): "1",
            name("birthday_day"): "2",
        }
    )
    form = DummyForm(data=data, prefix=prefix)

    data = form.fields["mosparo"].prepare_form_data(form)

    assert data["form_data"] == {
        name("appointment_0"): "2026-11-03",
        name("appointment_1"): "10:00",
        name("birthday_month"): "1",
        name("birthday_day"): "2",
        name("birthday_year"): "2000",
    }
    assert data["required_fields"] == [name("appointment_0"), name("appointment_1")]
    assert data["verifiable_fields"] == []


def test_mosparo_field_prepare_form_data_without_generated_id():
    # Without a generated id, the widget context has to be built as well.
    class DummyForm(Form):
        name = CharField()
        nickname = CharField(widget=TextInput(attrs={"id": "custom"}))
        mosparo = MosparoField()

    expected = {"name": "Test", "nickname": "Nick"}

    form = DummyForm(data=QueryDict("name=Test&nickname=Nick"))
    assert form.fields["mosparo"].prepare_form_data(form)["form_data"] == expected

    form = DummyForm(data=QueryDict("name=Test&nickname=Nick"), auto_id=False)
    assert form.fields["mosparo"].prepare_form_data(form)["form_data"] == expected


@pytest.mark.parametrize(
    "query, expected",
    [
        ("tags=a&tags=b", ["a", "b"]),
        ("tags=a", ["a"]),
        ("", []),
    ],
)
def test_mosparo_field_prepare_form_data_with_select_multiple(query, expected):
    # The frontend sends the selected options of a <select multiple> as a list,
    # also if only one or no option is selected.
    class DummyForm(Form):
        tags = MultipleChoiceField(choices=[("a", "A"), ("b", "B")], required=False)
        mosparo = MosparoField()

    form = DummyForm(data=QueryDict(query))

    data = form.fields["mosparo"].prepare_form_data(form)

    assert data["form_data"] == {"tags": expected}


def test_mosparo_field_prepare_form_data_with_select_multiple_and_dict():
    class DummyForm(Form):
        tags = MultipleChoiceField(choices=[("a", "A"), ("b", "B")])
        mosparo = MosparoField()

    form = DummyForm(data={"tags": ["a", "b"]})

    data = form.fields["mosparo"].prepare_form_data(form)

    assert data["form_data"] == {"tags": ["a", "b"]}
    assert data["required_fields"] == ["tags"]


def test_mosparo_field_verify_data_with_select_multiple(requests_mock):
    class DummyForm(Form):
        name = CharField(max_length=255)
        tags = MultipleChoiceField(choices=[("a", "A"), ("b", "B")])

    data = QueryDict(
        "name=Test&tags=a&tags=b&_mosparo_submitToken=submitToken&_mosparo_validationToken=validationToken"
    )
    form = DummyForm(data=data)
    form.is_valid()

    request_helper = RequestHelper("public_key", "private_key")
    prepared_form_data = request_helper.prepare_form_data(
        {"name": "Test", "tags": ["a", "b"]}
    )
    form_signature = request_helper.create_form_data_hmac_hash(prepared_form_data)
    validation_signature = request_helper.create_hmac_hash("validationToken")
    verification_signature = request_helper.create_hmac_hash(
        validation_signature + form_signature
    )

    requests_mock.post(
        "https://host.local/api/v1/verification/verify",
        json={
            "valid": True,
            "verificationSignature": verification_signature,
            "verifiedFields": {
                "name": VerificationResult.FIELD_VALID,
                "tags": VerificationResult.FIELD_VALID,
            },
            "issues": [],
        },
        status_code=200,
    )

    MosparoField().verify_data(form)

    assert requests_mock.last_request.json()["formData"] == prepared_form_data
