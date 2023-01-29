&nbsp;
<p align="center">
    <img src="https://github.com/mosparo/mosparo/blob/master/assets/images/mosparo-logo.svg?raw=true" alt="mosparo logo contains a bird with the name Mo and the mosparo text"/>
</p>

<h1 align="center">
    Integration for Django
</h1>
<p align="center">
    This Django app offers the needed form, field, and widget class to add mosparo to your Django form.
</p>

-----

## IMPORTANT: This is a very early alpha version. Please do not use it in production and send feedback as an issue or by email to feedback@mosparo.io.

## Description
With this Django app, you can protect your forms with mosparo. Install the app, configure it and add the field to your forms.

## Installation

### Install using pip

Install this app by using pip:

```commandline
pip install mosparo_django
```

### Build from source

1. Build the package
```commandline
python setup.py bdist_wheel 
```
2. Install the package
```commandline
pip install dist/mosparo_django-1.0.0-py3-none-any.whl
```

## Usage
1. Create a project in your mosparo installation
2. Edit the `settings.py` file of your project
2. Add the mosparo integration to the list of enabled apps:
```python
INSTALLED_APPS = [
    # ...
    'mosparo_django',
]
```
3. Specify the configuration for mosparo:
```python
MOSPARO_HOST = 'https://...'
MOSPARO_UUID = '...'
MOSPARO_PUBLIC_KEY = '...'
MOSPARO_PRIVATE_KEY = '...'
MOSPARO_VERIFY_SSL = True
```
4. Add the mosparo field to your form:
```python
from mosparo_django.fields import MosparoField

class Form(forms.Form):
    # Your other fields...
    mosparo = MosparoField(label='Spam protection')
```
5. Add the verification (see [Verification](#verification))
6. Test your form and verify that everything works correctly and you see the submission in mosparo.

### Verification

After the user submits the form, the backend has to verify the form data before you can process them. Since we didn't find a good way to do this automatically, you have to implement one of the following options:

#### Use the mosparo Form class

Use the mosparo Form class to create your form instead of the `django.forms.Form` class:

```python
from mosparo_django.forms import MosparoForm
from mosparo_django.fields import MosparoField

class Form(MosparoForm):
    # Your other fields...
    mosparo = MosparoField(label='Spam protection')
```

#### Override the `clean` method

The other option is to override the method `clean` of the Form class:

```python
from mosparo_django.fields import MosparoField

class Form(forms.Form):
    # Your other fields...
    mosparo_field = MosparoField(label='Spam protection')

    def clean(self):
        self.mosparo_field.verify_data(self)
    
        return super().clean()
```

**Important: No spam protection will happen if you do not use one of these two things.**

## License

mosparo Python API Client is open-sourced software licensed under the [MIT License](https://opensource.org/licenses/MIT).
Please see the [LICENSE](LICENSE) file for the full license.