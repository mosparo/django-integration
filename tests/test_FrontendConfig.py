from mosparo_django.config import FrontendConfig

def test_frontend_config():
    fc = FrontendConfig('https://test.local', 'test_uuid', 'test_public_key')

    assert 'https://test.local' == fc.get_host()
    assert 'test_uuid' == fc.get_uuid()
    assert 'test_public_key' == fc.get_public_key()