&nbsp;
<p align="center">
    <img src="https://github.com/mosparo/mosparo/blob/master/assets/images/mosparo-logo.svg?raw=true" alt="mosparo logo contains a bird with the name Mo and the mosparo text"/>
</p>

<h1 align="center">
    Integration for Django
</h1>
<p align="center">
    This Django app offers the needed field and widget class to add mosparo to your Django form.
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
pip install dist/mosparo_django-2.0.0-py3-none-any.whl
```

## Usage

1. Create a project in your mosparo installation
2. Edit the `settings.py` file of your project
2. Add the mosparo integration to the list of enabled apps:
```python
INSTALLED_APPS = [
    # ...
    "mosparo_django",
]
```
3. Specify the configuration for mosparo:
```python
MOSPARO_HOST = "https://..."
MOSPARO_UUID = "..."
MOSPARO_PUBLIC_KEY = "..."
MOSPARO_PRIVATE_KEY = "..."
MOSPARO_VERIFY_SSL = True
MOSPARO_TIMEOUT = 10  # Optional, in seconds. None waits without a limit.
```
4. Add the mosparo field to your form:
```python
from django import forms
from mosparo_django.fields import MosparoField


class Form(forms.Form):
    # Your other fields...
    mosparo = MosparoField(label="Spam protection")
```
5. Test your form and verify that everything works correctly and you see the submission in mosparo.

### Verification

The field verifies the submitted data with mosparo when the form is validated (for example, when calling `form.is_valid()`). If the verification fails, the error is attached to the mosparo field. No changes to the form class are needed, any `django.forms.Form` works.

### Fields sent to mosparo

The mosparo frontend collects the fields of the rendered form, and mosparo only accepts the submission if the backend sends exactly the same fields. The field therefore decides by the rendered HTML input type of each widget which fields it sends to mosparo:

- Inputs of the types `password`, `file`, `hidden`, `checkbox`, and `radio` are ignored, like in the frontend (e.g. `PasswordInput`, `FileInput`, `HiddenInput`, `CheckboxInput`, `RadioSelect`, `CheckboxSelectMultiple`).
- Inputs of the types `submit`, `reset`, and `button` are ignored, because the frontend doesn't collect them.
- All other fields are sent, including `<select>` and `<textarea>`. This also applies to a `NullBooleanField` or a `BooleanField` with a `Select` widget.
- Widgets which render several inputs (e.g. `SplitDateTimeWidget` or `SelectDateWidget`) are handled input by input, using the rendered names like `appointment_0` and `appointment_1`.
- The selected options of a `<select multiple>` (e.g. `MultipleChoiceField`) are sent as a list, like the frontend collects them.

To ignore any other field, add the CSS class `mosparo__ignored-field` to its widget:

```python
email = forms.EmailField(
    widget=forms.EmailInput(attrs={"class": "mosparo__ignored-field"}),
)
```

The class has to be set on the widget in the form class. A class that is only added in the template (e.g. by a template tag) isn't visible to the backend, the verification would fail.

If you changed the field selector of the mosparo frontend, the backend has to send the same fields. Use `callback_after_prepare_form_data` (see below) to adjust the form data accordingly.

### Specify the connection details on the field

You can also specify the connection details on the field. For that, please add the field to your form and specify the connection settings by setting the parameters `mosparo_host`, `mosparo_uuid`, `mosparo_public_key`, `mosparo_private_key`, `mosparo_verify_ssl`, and `mosparo_timeout`. If you want to change the UUID, public or private key, you have to specify all these three values because these depend on the project and if you want to connect the field to a different project, all three values will be different.

```python
from django import forms
from mosparo_django.fields import MosparoField


class Form(forms.Form):
    # Your other fields...
    mosparo = MosparoField(
        label="Spam protection",
        mosparo_uuid="123",
        mosparo_public_key="test_key",
        mosparo_private_key="private_key",
    )
```

### Filter the field types and form data

The MosparoField offers some callback methods to adjust the behavior of the field.

```python
from django import forms
from mosparo_django.fields import MosparoField


class Form(forms.Form):
    # Your other fields...
    mosparo = MosparoField(
        callback_verifiable_field_types=None,
        callback_after_prepare_form_data=None,
    )
```

| Argument name                      | Description                                                                                                                                          |
|------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| `callback_verifiable_field_types`  | Gets and returns a list of field or widget classes which are verifiable, including their subclasses (Example: `forms.TextInput`)                    |
| `callback_after_prepare_form_data` | Gets the dict with all prepared form data, the required field names, and the verifiable field names as argument and expects the same to be returned. |

## Upgrade from 1.x to 2.0

- Python 3.10 or newer is required.
- `mosparo-api-client` 1.2 or newer is required. Requests to mosparo now time out after 10 seconds, after which the field shows the "currently unavailable" error. Use the setting `MOSPARO_TIMEOUT` or the argument `mosparo_timeout` to change this.
- `mosparo_django.forms.MosparoForm` was removed. Use a regular `django.forms.Form`, the `MosparoField` verifies the submission itself. Remove manual calls of `verify_data()` in `Form.clean()`, they aren't needed anymore.
- If the verification fails, the error is attached to the mosparo field instead of the non-field errors.
- The argument `mosparo_timeout` was added directly after `mosparo_verify_ssl` to configure the timeout of the connection to the mosparo server.
- The argument `callback_ignored_field_types` was removed. Fields are now ignored by their rendered HTML input type (see [Fields sent to mosparo](#fields-sent-to-mosparo)). To ignore additional fields, add the CSS class `mosparo__ignored-field` to the widget.
- A `NullBooleanField` and a `BooleanField` with a `Select` widget are now sent to mosparo, because the frontend collects them as well.
- Fields with a `MultiWidget` or a `SelectDateWidget` are now sent with the names of their rendered inputs (e.g. `appointment_0`, `appointment_1`). Before, the verification of forms with such fields failed.
- `callback_verifiable_field_types` only accepts field or widget classes. Class names as strings raise an `ImproperlyConfigured` error.
- The field no longer sets the undocumented attribute `form.valid`. Use `form.is_valid()` or `form.errors` instead.

## License

mosparo Integration for Django is open-sourced software licensed under the [MIT License](https://opensource.org/licenses/MIT).
Please see the [LICENSE](LICENSE) file for the full license.

## Contributing

### Translate mosparo Integration for Django

We're using [Weblate](https://weblate.org/) to translate the mosparo Integration for Django. If you want to help translate the mosparo Integration for Django, please head over to our Weblate project: https://hosted.weblate.org/projects/mosparo/integration_django/

#### List of translators

| Language  | Language Code | Contributors                                                             |
|-----------|---------------|--------------------------------------------------------------------------|
| German    | de            | mosparo Core Developers                                                  |
| Estonian  | et            | [jrthwlate](https://hosted.weblate.org/user/jrthwlate/)                  |
| French    | fr            | [Bamowen](https://hosted.weblate.org/user/Bamowen/)                      |
| Croatian  | hr            | [milotype](https://hosted.weblate.org/user/milotype/)                    |
| Korean    | ko            | [MarongHappy](https://hosted.weblate.org/user/MarongHappy/)              |
| Tamil     | ta            | [TamilNeram](https://hosted.weblate.org/user/TamilNeram/)                |
| Turkish   | tr            | [ersen](https://hosted.weblate.org/user/ersen/), mosparo Core Developers |
| Ukrainian | uk            | [kefir2105](https://hosted.weblate.org/user/kefir2105/)                  |

Thank you for helping to make the mosparo Integration for Django better.
