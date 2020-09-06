import json
from typing import List, Tuple

from django import forms
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from wagtail.core import blocks

from wagtailseo import schema


class MultiSelectBlock(blocks.FieldBlock):
    """
    Renders as MultipleChoiceField, used for adding checkboxes,
    radios, or multiselect inputs in the streamfield.
    """

    def __init__(
        self,
        required: bool = True,
        help_text: str = None,
        choices: List[Tuple[str, str]] = None,
        widget=None,
        **kwargs
    ):
        self.field = forms.MultipleChoiceField(
            required=required,
            help_text=help_text,
            choices=choices,
            widget=widget,
        )
        super().__init__(**kwargs)

    def get_searchable_content(self, value):
        return [force_str(value)]


class OpenHoursValue(blocks.StructValue):
    """
    Renders selected days as a json list.
    """

    @property
    def days_json(self):
        """
        Custom property to return days as json list instead of default python list.
        """
        return json.dumps(self["days"])


class OpenHoursBlock(blocks.StructBlock):
    """
    Holds day and time combination for business open hours.
    """

    class Meta:
        template = "wagtailseo/struct_data_hours.json"
        label = _("Open Hours")
        value_class = OpenHoursValue

    days = MultiSelectBlock(
        required=True,
        verbose_name=_("Days"),
        help_text=_(
            "For late night hours past 23:59, define each day in a separate block."
        ),
        widget=forms.CheckboxSelectMultiple,
        choices=[
            ("Monday", _("Monday")),
            ("Tuesday", _("Tuesday")),
            ("Wednesday", _("Wednesday")),
            ("Thursday", _("Thursday")),
            ("Friday", _("Friday")),
            ("Saturday", _("Saturday")),
            ("Sunday", _("Sunday")),
        ],
    )
    start_time = blocks.TimeBlock(verbose_name=_("Opening time"))
    end_time = blocks.TimeBlock(verbose_name=_("Closing time"))


class StructuredDataActionBlock(blocks.StructBlock):
    """
    Action object from schema.org
    """

    class Meta:
        template = "wagtailseo/struct_data_action.json"
        label = _("Action")

    action_type = blocks.ChoiceBlock(
        verbose_name=_("Action Type"),
        required=True,
        choices=schema.SCHEMA_ACTION_CHOICES,
    )
    target = blocks.URLBlock(
        verbose_name=_("Target URL"),
    )
    language = blocks.CharBlock(
        verbose_name=_("Language"),
        help_text=_(
            "If the action is offered in multiple languages, create separate "
            "actions for each language."
        ),
        default="en-US",
    )
    result_type = blocks.ChoiceBlock(
        required=False,
        verbose_name=_("Result Type"),
        help_text=_("Leave blank for OrderAction"),
        choices=schema.SCHEMA_RESULT_CHOICES,
    )
    result_name = blocks.CharBlock(
        required=False,
        verbose_name=_("Result Name"),
        help_text=_('Example: "Reserve a table", "Book an appointment", etc.'),
    )
    extra_json = blocks.RawHTMLBlock(
        required=False,
        verbose_name=_("Additional action markup"),
        classname="monospace",
        help_text=_(
            "Additional JSON-LD inserted into the Action dictionary. "
            "Must be properties of https://schema.org/Action."
        ),
    )