from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

__project__ = "mosparo_django"
__version__ = "1.0.9"

settings_types = {
    "MOSPARO_HOST": str,
    "MOSPARO_UUID": str,
    "MOSPARO_PUBLIC_KEY": str,
    "MOSPARO_PRIVATE_KEY": str,
    "MOSPARO_VERIFY_SSL": bool,
}

required_settings = [
    "MOSPARO_HOST",
    "MOSPARO_UUID",
    "MOSPARO_PUBLIC_KEY",
    "MOSPARO_PRIVATE_KEY",
]

for setting, type in settings_types.items():
    if not hasattr(settings, setting) and setting in required_settings:
        raise ImproperlyConfigured(f'Setting "{setting}" is not defined.')

    if hasattr(settings, setting) and not isinstance(getattr(settings, setting), type):
        raise ImproperlyConfigured(
            f'Type of Setting "{setting}" is not correct. Should be "{type}".'
        )
