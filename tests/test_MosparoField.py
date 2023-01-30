from django.forms import Form, Widget, CharField
from django.core.exceptions import ImproperlyConfigured, ValidationError
import pytest

from mosparo import RequestHelper, VerificationResult

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

    form = DummyForm(data={
        'name': 'Test',
        '_mosparo_submitToken': 'submitToken',
        '_mosparo_validationToken': 'validationToken'
    })
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


def test_mosparo_field_verify_data_validation_error(requests_mock):
    # Prepare the form
    class DummyForm(Form):
        name = CharField(label='Name', max_length=255)

    form = DummyForm(data={
        'name': 'Test',
        '_mosparo_submitToken': 'submitToken',
        '_mosparo_validationToken': 'validationToken'
    })
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

