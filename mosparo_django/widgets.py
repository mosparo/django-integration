import uuid

from django.forms import widgets

from mosparo_django.config import FrontendConfig

class MosparoWidget(widgets.Widget):
    template_name = 'mosparo/box.html'

    frontend_config = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.uuid = uuid.uuid4().hex

    def set_frontend_config(self, frontend_config: FrontendConfig):
        self.frontend_config = frontend_config

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context.update(
            {
                'widget_uuid': self.uuid,
                'mosparo_host': self.frontend_config.get_host(),
                'mosparo_uuid': self.frontend_config.get_uuid(),
                'mosparo_public_key': self.frontend_config.get_public_key()
            }
        )
        return context
