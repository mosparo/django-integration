import uuid

from django.conf import settings
from django.forms import widgets

class MosparoWidget(widgets.Widget):
    template_name = 'mosparo/box.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.uuid = uuid.uuid4().hex

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context.update(
            {
                'widget_uuid': self.uuid,
                'mosparo_host': getattr(settings, 'MOSPARO_HOST', ''),
                'mosparo_uuid': getattr(settings, 'MOSPARO_UUID', ''),
                'mosparo_public_key': getattr(settings, 'MOSPARO_PUBLIC_KEY', '')
            }
        )
        return context
