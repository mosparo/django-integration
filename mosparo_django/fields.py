import logging
import weakref

import requests
from django import forms
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.utils.translation import gettext_lazy as _
from mosparo_api_client import Client, MosparoException

from mosparo_django.config import FrontendConfig
from mosparo_django.widgets import MosparoWidget

logger = logging.getLogger(__name__)

# The mosparo frontend doesn't collect inputs of these types.
SKIPPED_INPUT_TYPES = frozenset({"submit", "reset", "button"})

# The mosparo frontend collects inputs of these types as ignored fields, so
# they aren't part of the verified form data.
IGNORED_INPUT_TYPES = frozenset({"password", "file", "hidden", "checkbox", "radio"})

# Fields with this class are ignored additionally.
IGNORED_FIELD_CLASS = "mosparo__ignored-field"

# The timeout in seconds for the requests to mosparo.
DEFAULT_TIMEOUT = 10


class MosparoField(forms.BooleanField):
    widget = MosparoWidget

    mosparo_host = None
    mosparo_uuid = None
    mosparo_public_key = None
    mosparo_private_key = None
    mosparo_verify_ssl = True
    mosparo_timeout = DEFAULT_TIMEOUT

    callback_verifiable_field_types = None
    callback_after_prepare_form_data = None

    _form = None
    _verified_form = None
    _verification_error = None

    def __init__(
        self,
        mosparo_host=None,
        mosparo_uuid=None,
        mosparo_public_key=None,
        mosparo_private_key=None,
        mosparo_verify_ssl=None,
        mosparo_timeout=None,
        callback_verifiable_field_types=None,
        callback_after_prepare_form_data=None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        if not isinstance(self.widget, MosparoWidget):
            raise ImproperlyConfigured(
                "The widget must be a subclass of mosparo_django.widgets.MosparoWidget"
            )

        if mosparo_host is None:
            mosparo_host = getattr(settings, "MOSPARO_HOST", "")

        if (
            mosparo_uuid is None
            or mosparo_public_key is None
            or mosparo_private_key is None
        ):
            mosparo_uuid = getattr(settings, "MOSPARO_UUID", "")
            mosparo_public_key = getattr(settings, "MOSPARO_PUBLIC_KEY", "")
            mosparo_private_key = getattr(settings, "MOSPARO_PRIVATE_KEY", "")

        if mosparo_verify_ssl is None:
            mosparo_verify_ssl = getattr(settings, "MOSPARO_VERIFY_SSL", True)

        if mosparo_timeout is None:
            mosparo_timeout = getattr(settings, "MOSPARO_TIMEOUT", DEFAULT_TIMEOUT)

        self.mosparo_host = mosparo_host
        self.mosparo_uuid = mosparo_uuid
        self.mosparo_public_key = mosparo_public_key
        self.mosparo_private_key = mosparo_private_key
        self.mosparo_verify_ssl = mosparo_verify_ssl
        self.mosparo_timeout = mosparo_timeout

        self.callback_verifiable_field_types = callback_verifiable_field_types
        self.callback_after_prepare_form_data = callback_after_prepare_form_data

        frontend_config = FrontendConfig(
            self.mosparo_host, self.mosparo_uuid, self.mosparo_public_key
        )
        self.widget.set_frontend_config(frontend_config)

        # Hide the label for the field, important for the invisible mode.
        self.label = ""

    def get_bound_field(self, form, field_name):
        # Remember the form so that clean() can verify the whole submission.
        # Each form instance works on its own deep copy of the fields.
        self._form = weakref.ref(form)
        return super().get_bound_field(form, field_name)

    def validate(self, value):
        return True

    def clean(self, value):
        value = super().clean(value)

        form = self._form() if self._form is not None else None
        if form is None:
            raise ImproperlyConfigured(
                "MosparoField can only be cleaned as part of a form."
            )

        self.verify_data(form)
        return value

    def verify_data(self, form: forms.Form):
        # A submission can only be verified once, so the result is remembered
        # for this form instance (e.g. when full_clean() is called again).
        if self._verified_form is not None and self._verified_form() is form:
            if self._verification_error is not None:
                raise self._verification_error
            return

        try:
            self._verify_submission(form)
        except (MosparoException, requests.exceptions.RequestException):
            # mosparo couldn't be reached or returned an invalid response. This
            # isn't a verification result, so it isn't remembered and a later
            # validation of the form asks mosparo again.
            logger.exception("The submission could not be verified with mosparo.")

            raise ValidationError(
                _(
                    "The spam protection is currently unavailable. Please try again later."
                ),
                code="mosparo_unavailable",
            )
        except ValidationError as e:
            self._verification_error = e
            self._verified_form = weakref.ref(form)
            raise

        self._verification_error = None
        self._verified_form = weakref.ref(form)

    def _verify_submission(self, form: forms.Form):
        api_client = Client(
            self.mosparo_host,
            self.mosparo_public_key,
            self.mosparo_private_key,
            self.mosparo_verify_ssl,
            timeout=self.mosparo_timeout,
        )

        if (
            "_mosparo_submitToken" not in form.data
            or "_mosparo_validationToken" not in form.data
        ):
            raise ValidationError(
                _("mosparo specific fields were not found in the submitted data.")
            )

        data = self.prepare_form_data(form)
        submit_token = form.data["_mosparo_submitToken"]
        validation_token = form.data["_mosparo_validationToken"]

        res = api_client.verify_submission(
            data["form_data"], submit_token, validation_token
        )

        if res is not None:
            verified_fields = res.get_verified_fields()
            required_field_difference = set(data["required_fields"]) - set(
                verified_fields.keys()
            )
            verifiable_field_difference = set(data["verifiable_fields"]) - set(
                verified_fields.keys()
            )

            # The submission is only valid if all required and verifiable fields got verified
            if (
                res.is_submittable()
                and not required_field_difference
                and not verifiable_field_difference
            ):
                return

        raise ValidationError(_("The spam protection could not verify the data."))

    def get_mosparo_host(self):
        return self.mosparo_host

    def get_mosparo_uuid(self):
        return self.mosparo_uuid

    def get_mosparo_public_key(self):
        return self.mosparo_public_key

    def prepare_form_data(self, form: forms.Form):
        data = {"form_data": {}, "required_fields": [], "verifiable_fields": []}

        verifiable_field_types = [
            forms.TextInput,
            forms.Textarea,
            forms.EmailInput,
            forms.URLInput,
        ]
        if self.callback_verifiable_field_types is not None:
            verifiable_field_types = self.callback_verifiable_field_types(
                verifiable_field_types
            )

        verifiable_field_types = _to_type_tuple(verifiable_field_types)

        for key, field in form.fields.items():
            # The mosparo field itself renders no input which the frontend collects.
            if isinstance(field, MosparoField):
                continue

            is_verifiable = isinstance(field, verifiable_field_types) or isinstance(
                field.widget, verifiable_field_types
            )

            name = form.add_prefix(key)

            # A widget can render several inputs, e.g. a MultiWidget renders "name_0" and "name_1".
            # The frontend collects each of them.
            for name, input_type, attrs in _rendered_inputs(form[key]):
                if _is_ignored_input(input_type, attrs):
                    continue

                if field.required:
                    data["required_fields"].append(name)

                if is_verifiable:
                    data["verifiable_fields"].append(name)

                if _is_multiple_select(input_type, attrs):
                    # The frontend sends the selected options of a <select multiple> as a list, even if none is selected.
                    data["form_data"][name] = _get_list(form.data, name)
                elif name in form.data:
                    data["form_data"][name] = form.data[name]

        if self.callback_after_prepare_form_data is not None:
            data = self.callback_after_prepare_form_data(data)

        return data


def _rendered_inputs(bound_field):
    """
    Yields the name, the input type and the attributes of each input which the bound field renders.
    The widget context is built like when the field is rendered, so that the result matches the
    HTML which the frontend sees.
    """
    widget = bound_field.field.widget
    attrs = bound_field.build_widget_attrs({}, widget)

    if bound_field.auto_id and "id" not in widget.attrs:
        attrs["id"] = bound_field.auto_id

    context = widget.get_context(bound_field.html_name, bound_field.value(), attrs)

    yield from _walk_widget_context(context["widget"])


def _walk_widget_context(context):
    # MultiWidget and SelectDateWidget render one input per subwidget.
    if context.get("subwidgets"):
        for subwidget in context["subwidgets"]:
            yield from _walk_widget_context(subwidget)
        return

    input_type = context.get("type")
    if input_type is None:
        # Choice widgets (e.g. RadioSelect) store the type on their options.
        for _group_name, options, _index in context.get("optgroups", ()):
            if options:
                input_type = options[0].get("type")
                break

    yield context["name"], input_type, context["attrs"]


def _is_ignored_input(input_type, attrs):
    """
    Returns True if the input must not be sent to mosparo. This has to match the inputs which the
    mosparo frontend ignores in the rendered form, otherwise the verification fails.
    """
    if input_type in SKIPPED_INPUT_TYPES or input_type in IGNORED_INPUT_TYPES:
        return True

    return IGNORED_FIELD_CLASS in str(attrs.get("class", "")).split()


def _is_multiple_select(input_type, attrs):
    # Inputs have a type in their context, a <select> only on its options.
    return input_type in (None, "select") and bool(attrs.get("multiple"))


def _get_list(form_data, name):
    # Like SelectMultiple.value_from_datadict(), form.data can be a QueryDict or a plain dict.
    if hasattr(form_data, "getlist"):
        return form_data.getlist(name)

    value = form_data.get(name, [])
    return list(value) if isinstance(value, (list, tuple)) else [value]


def _to_type_tuple(field_types):
    for field_type in field_types:
        if not isinstance(field_type, type):
            raise ImproperlyConfigured(
                f"Field types must be field or widget classes, got {field_type!r}."
            )

    return tuple(field_types)
