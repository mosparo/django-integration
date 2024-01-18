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

## Description

With this Django app, you can protect your forms with mosparo. Install the app, configure it and add the field to your forms.

## How to use

Please see our [How to use](https://mosparo.io/how-to-use/) introduction on our website to learn how to use mosparo in your form.

In step 3 of the how-to-use explanation, you must integrate mosparo into your website. Please follow the [Installation](#installation) part below for this process.

In step 4 of the how-to-use explanation, you must connect your website with your mosparo project. Please follow the [Usage](#usage) part below.

## Installation

### Install using pip

Install this app by using pip:

```commandline
pip install mosparo_django
```

### Build from source

You need the module `build` to build the module from source.

1. Clone the repository
2. Build the package
```commandline
python -m build
```
3. Install the package
```commandline
pip install dist/mosparo_django-1.0.0b1-py3-none-any.whl
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
    mosparo = MosparoField(label='Spam protection')

    def clean(self):
        self.mosparo.verify_data(self)
    
        return super().clean()
```

**Important: No spam protection will happen if you do not use one of these two things.**

### Specify the connection details on the field

You can also specify the connection details on the field. For that, please add the field to your form and specify the connection settings by setting the parameters `mosparo_host`, `mosparo_uuid`, `mosparo_public_key`, `mosparo_private_key`, and `mosparo_verify_ssl`. If you want to change the UUID, public or private key, you have to specify all these three values because these depend on the project and if you want to connect the field to a different project, all three values will be different.

```python
from mosparo_django.forms import MosparoForm
from mosparo_django.fields import MosparoField

class Form(MosparoForm):
    # Your other fields...
    mosparo = MosparoField(label='Spam protection', mosparo_uuid='123', mosparo_public_key='test_key', mosparo_private_key = 'private_key')
```

### Filter the field types and form data

The MosparoField offers some callback methods to adjust the behavior of the field.

```python
from mosparo_django.forms import MosparoForm
from mosparo_django.fields import MosparoField

class Form(MosparoForm):
    # Your other fields...
    mosparo = MosparoField(callback_ignored_field_types=None, callback_verifiable_field_types=None, callback_after_prepare_form_data=None)
```

| Argument name                      | Description                                                                                                                                          |
|------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| `callback_ignored_field_types`     | Gets and returns a list of class names of field types, which should be ignored (Example: `PasswordInput`)                                            |
| `callback_verifiable_field_types`  | Gets and returns a list of class names of field types, which are verifiable (Example: `TextInput`)                                                   |
| `callback_after_prepare_form_data` | Gets the dict with all prepared form data, the required field names, and the verifiable field names as argument and expects the same to be returned. |

## License

mosparo Integration for Django is open-sourced software licensed under the [MIT License](https://opensource.org/licenses/MIT).
Please see the [LICENSE](LICENSE) file for the full license.