from mosparo_django.config import FrontendConfig
from mosparo_django.widgets import MosparoWidget

def test_mosparo_widget():
    fc = FrontendConfig('https://test.local', 'test_uuid', 'test_public_key')

    mw = MosparoWidget()
    mw.set_frontend_config(fc)

    context = mw.get_context('test', {}, {})

    assert 'https://test.local' == context['mosparo_host']
    assert 'test_uuid' == context['mosparo_uuid']
    assert 'test_public_key' == context['mosparo_public_key']
    assert 'mosparo/box.html' == mw.template_name
