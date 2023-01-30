DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}

INSTALLED_APPS = [
    'mosparo_django',
]

LANGUAGE_CODE = 'en-US'
TIME_ZONE = 'Europe/Zurich'
USE_I18N = True
USE_TZ = True

SECRET_KEY = 'test123'

MOSPARO_HOST = 'https://host.local'
MOSPARO_UUID = 'uuid'
MOSPARO_PUBLIC_KEY = 'public_key'
MOSPARO_PRIVATE_KEY = 'private_key'
MOSPARO_VERIFY_SSL = False
