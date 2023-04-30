from django.forms import Form, Widget, CharField, URLField, PasswordInput, TextInput
from django.core.exceptions import ImproperlyConfigured, ValidationError
import pytest
from django.http import QueryDict

from mosparo_api_client import RequestHelper, VerificationResult

from mosparo_django.fields import MosparoField

def test_mosparo_field():
    mf = MosparoField()

    assert 'https://host.local' == mf.get_mosparo_host()
    assert 'uuid' == mf.get_mosparo_uuid()
    assert 'public_key' == mf.get_mosparo_public_key()
    assert mf.validate(1) is True

def test_mosparo_field_custom_args():
    mf = MosparoField(mosparo_host='https://custom-test.local', mosparo_uuid='custom_uuid',
                      mosparo_public_key='custom_public_key', mosparo_private_key='custom_private_key')

    assert 'https://custom-test.local' == mf.get_mosparo_host()
    assert 'custom_uuid' == mf.get_mosparo_uuid()
    assert 'custom_public_key' == mf.get_mosparo_public_key()
    assert mf.validate(1) is True

    assert 'https://custom-test.local' == mf.widget.frontend_config.get_host()
    assert 'custom_uuid' == mf.widget.frontend_config.get_uuid()
    assert 'custom_public_key' == mf.widget.frontend_config.get_public_key()

def test_mosparo_field_custom_widget():
    class CustomMosparoField(MosparoField):
        widget = Widget

    with pytest.raises(ImproperlyConfigured) as exc:
        mf = CustomMosparoField()

    assert 'The widget must be a subclass of mosparo_django.widgets.MosparoWidget' in str(exc.value)

def test_mosparo_field_verify_data_without_mosparo_tokens():
    class DummyForm(Form):
        data = {'name': 'Test'}

    form = DummyForm()
    mf = MosparoField()

    with pytest.raises(ValidationError) as exc:
        mf.verify_data(form)

    assert 'mosparo specific fields were not found in the submitted data.' in str(exc.value)

def test_mosparo_field_verify_data(requests_mock):
    # Prepare the form
    class DummyForm(Form):
        name = CharField(label='Name', max_length=255)
        password = CharField(label='Password', max_length=255, widget=PasswordInput)

    data = QueryDict('name=Test&_mosparo_submitToken=submitToken&_mosparo_validationToken=validationToken')
    form = DummyForm(data=data)

    form.is_valid()

    # Prepare the API request
    public_key = 'public_key'
    private_key = 'private_key'
    validation_token = 'validationToken'
    form_data = {'name': 'Test'}

    request_helper = RequestHelper(public_key, private_key)

    prepared_form_data = request_helper.prepare_form_data(form_data)
    form_signature = request_helper.create_form_data_hmac_hash(prepared_form_data)

    validation_signature = request_helper.create_hmac_hash(validation_token)
    verification_signature = request_helper.create_hmac_hash(validation_signature + form_signature)

    requests_mock.post('https://host.local/api/v1/verification/verify', json={
        'valid': True,
        'verificationSignature': verification_signature,
        'verifiedFields': {'name': VerificationResult.FIELD_VALID},
        'issues': []
    }, status_code=200)

    mf = MosparoField()
    mf.verify_data(form)

def test_mosparo_field_verify_data_with_ignored_callback(requests_mock):
    # Prepare the form
    class DummyForm(Form):
        name = CharField(label='Name', max_length=255)
        password = CharField(label='Password', max_length=255, widget=PasswordInput)

    data = QueryDict('name=Test&_mosparo_submitToken=submitToken&_mosparo_validationToken=validationToken')
    form = DummyForm(data=data)

    form.is_valid()

    # Prepare the API request
    public_key = 'public_key'
    private_key = 'private_key'
    validation_token = 'validationToken'
    form_data = {'name': 'Test'}

    request_helper = RequestHelper(public_key, private_key)

    prepared_form_data = request_helper.prepare_form_data(form_data)
    form_signature = request_helper.create_form_data_hmac_hash(prepared_form_data)

    validation_signature = request_helper.create_hmac_hash(validation_token)
    verification_signature = request_helper.create_hmac_hash(validation_signature + form_signature)

    requests_mock.post('https://host.local/api/v1/verification/verify', json={
        'valid': True,
        'verificationSignature': verification_signature,
        'verifiedFields': {'name': VerificationResult.FIELD_VALID},
        'issues': []
    }, status_code=200)

    def test_callback(types):
        return []

    mf = MosparoField(callback_ignored_field_types=test_callback)

    with pytest.raises(ValidationError) as exc:
        # Fails because the password field was not ignored and was missing in the list of verified fields
        mf.verify_data(form)

    assert 'mosparo could not verify the data. Please check the submission in mosparo.' in str(exc.value)

def test_mosparo_field_verify_data_with_verifiable_callback(requests_mock):
    class TestInput(TextInput):
        pass

    # Prepare the form
    class DummyForm(Form):
        name = CharField(label='Name', max_length=255)
        url = URLField(label='URL', max_length=255, required=False)
        test_field = CharField(label='Test', max_length=255, required=False, widget=TestInput)

    data = QueryDict('name=Test&_mosparo_submitToken=submitToken&_mosparo_validationToken=validationToken')
    form = DummyForm(data=data)

    form.is_valid()

    # Prepare the API request
    public_key = 'public_key'
    private_key = 'private_key'
    validation_token = 'validationToken'
    form_data = {'name': 'Test'}

    request_helper = RequestHelper(public_key, private_key)

    prepared_form_data = request_helper.prepare_form_data(form_data)
    form_signature = request_helper.create_form_data_hmac_hash(prepared_form_data)

    validation_signature = request_helper.create_hmac_hash(validation_token)
    verification_signature = request_helper.create_hmac_hash(validation_signature + form_signature)

    requests_mock.post('https://host.local/api/v1/verification/verify', json={
        'valid': True,
        'verificationSignature': verification_signature,
        'verifiedFields': {'name': VerificationResult.FIELD_VALID, 'url': VerificationResult.FIELD_VALID},
        'issues': []
    }, status_code=200)

    def test_callback(types):
        # Add TestInput to the list of verifiable fields
        return types + ['TestInput']

    mf = MosparoField(callback_verifiable_field_types=test_callback)

    with pytest.raises(ValidationError) as exc:
        mf.verify_data(form)

    # Fails, because not all verifiable fields got verified (the TestInput field type was missing)
    assert 'mosparo could not verify the data. Please check the submission in mosparo.' in str(exc.value)

def test_mosparo_field_verify_data_with_after_data_callback(requests_mock):
    class TestInput(TextInput):
        pass

    # Prepare the form
    class DummyForm(Form):
        name = CharField(label='Name', max_length=255)
        url = URLField(label='URL', max_length=255, required=False)
        test_field = CharField(label='Test', max_length=255, required=False, widget=TestInput)

    data = QueryDict('name=Test&_mosparo_submitToken=submitToken&_mosparo_validationToken=validationToken')
    form = DummyForm(data=data)

    form.is_valid()

    # Prepare the API request
    public_key = 'public_key'
    private_key = 'private_key'
    validation_token = 'validationToken'
    form_data = {'name': 'Test'}

    request_helper = RequestHelper(public_key, private_key)

    prepared_form_data = request_helper.prepare_form_data(form_data)
    form_signature = request_helper.create_form_data_hmac_hash(prepared_form_data)

    validation_signature = request_helper.create_hmac_hash(validation_token)
    verification_signature = request_helper.create_hmac_hash(validation_signature + form_signature)

    requests_mock.post('https://host.local/api/v1/verification/verify', json={
        'valid': True,
        'verificationSignature': verification_signature,
        'verifiedFields': {'name': VerificationResult.FIELD_VALID, 'url': VerificationResult.FIELD_VALID},
        'issues': []
    }, status_code=200)

    def test_callback(data):
        data['required_fields'].append('test-field')
        return data

    mf = MosparoField(callback_after_prepare_form_data=test_callback)

    with pytest.raises(ValidationError) as exc:
        mf.verify_data(form)

    # Fails, because
    assert 'mosparo could not verify the data. Please check the submission in mosparo.' in str(exc.value)

def test_mosparo_field_verify_data_validation_error(requests_mock):
    # Prepare the form
    class DummyForm(Form):
        name = CharField(label='Name', max_length=255)

    data = QueryDict('name=Test&_mosparo_submitToken=submitToken&_mosparo_validationToken=validationToken')
    form = DummyForm(data=data)

    form.is_valid()

    # Prepare the API request
    public_key = 'public_key'
    private_key = 'private_key'
    validation_token = 'validationToken'
    form_data = {'name': 'Test'}

    request_helper = RequestHelper(public_key, private_key)

    prepared_form_data = request_helper.prepare_form_data(form_data)
    form_signature = request_helper.create_form_data_hmac_hash(prepared_form_data)

    validation_signature = request_helper.create_hmac_hash(validation_token)
    verification_signature = request_helper.create_hmac_hash(validation_signature + form_signature)

    requests_mock.post('https://host.local/api/v1/verification/verify', json={
        'valid': False,
        'verificationSignature': verification_signature,
        'verifiedFields': {'name': VerificationResult.FIELD_VALID},
        'issues': []
    }, status_code=200)

    mf = MosparoField()

    with pytest.raises(ValidationError) as exc:
        mf.verify_data(form)

    assert 'mosparo could not verify the data. Please check the submission in mosparo.' in str(exc.value)

