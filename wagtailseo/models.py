from enum import Enum

from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.edit_handlers import (
    HelpPanel,
    FieldPanel,
    MultiFieldPanel,
    StreamFieldPanel,
)
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.core.fields import StreamField
from wagtail.core.models import Page
from wagtail.images import get_image_model_string
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.images.models import AbstractImage

from wagtailseo import schema, utils
from wagtailseo.blocks import OpenHoursBlock, StructuredDataActionBlock
from wagtailseo.icon import SEO_ICON


class OpenGraphType(Enum):
    ARTICLE = "article"
    WEBSITE = "website"


class TwitterCard(Enum):
    APP = "app"
    LARGE = "summary_large_image"
    PLAYER = "player"
    SUMMARY = "summary"


class SeoMixin(Page):
    """
    Contains fields for SEO-related attributes on a Page model.
    """

    class Meta:
        abstract = True

    og_image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Preview image"),
        help_text=_("Shown when linking to this page on social media."),
    )
    struct_org_type = models.CharField(
        default="",
        blank=True,
        max_length=255,
        choices=schema.SCHEMA_ORG_CHOICES,
        verbose_name=_("Organization type"),
        help_text=_("If blank, no structured data will be used on this page."),
    )
    struct_org_name = models.CharField(
        default="",
        blank=True,
        max_length=255,
        verbose_name=_("Organization name"),
        help_text=_("Leave blank to use the site name in Settings > Sites"),
    )
    struct_org_logo = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Organization logo"),
        help_text=_("Leave blank to use the logo in Settings > Layout > Logo"),
    )
    struct_org_image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Photo of Organization"),
        help_text=_(
            "A photo of the facility. This photo will be cropped to 1:1, 4:3, "
            "and 16:9 aspect ratios automatically."
        ),
    )
    struct_org_phone = models.CharField(
        blank=True,
        max_length=255,
        verbose_name=_("Telephone number"),
        help_text=_(
            "Include country code for best results. For example: +1-216-555-8000"
        ),
    )
    struct_org_address_street = models.CharField(
        blank=True,
        max_length=255,
        verbose_name=_("Street address"),
        help_text=_(
            "House number and street. For example, 55 Public Square Suite 1710"
        ),
    )
    struct_org_address_locality = models.CharField(
        blank=True,
        max_length=255,
        verbose_name=_("City"),
        help_text=_("City or locality. For example, Cleveland"),
    )
    struct_org_address_region = models.CharField(
        blank=True,
        max_length=255,
        verbose_name=_("State"),
        help_text=_("State, province, county, or region. For example, OH"),
    )
    struct_org_address_postal = models.CharField(
        blank=True,
        max_length=255,
        verbose_name=_("Postal code"),
        help_text=_("Zip or postal code. For example, 44113"),
    )
    struct_org_address_country = models.CharField(
        blank=True,
        max_length=255,
        verbose_name=_("Country"),
        help_text=_(
            "For example, USA. Two-letter ISO 3166-1 alpha-2 country code is "
            "also acceptable https://en.wikipedia.org/wiki/ISO_3166-1"
        ),
    )
    struct_org_geo_lat = models.DecimalField(
        blank=True,
        null=True,
        max_digits=10,
        decimal_places=8,
        verbose_name=_("Geographic latitude"),
    )
    struct_org_geo_lng = models.DecimalField(
        blank=True,
        null=True,
        max_digits=10,
        decimal_places=8,
        verbose_name=_("Geographic longitude"),
    )
    struct_org_hours = StreamField(
        [("hours", OpenHoursBlock())],
        blank=True,
        verbose_name=_("Hours of operation"),
    )
    struct_org_actions = StreamField(
        [("actions", StructuredDataActionBlock())],
        blank=True,
        verbose_name=_("Actions"),
    )
    struct_org_extra_json = models.TextField(
        blank=True,
        verbose_name=_("Additional Organization markup"),
        help_text=_(
            "Additional JSON-LD inserted into the Organization dictionary. "
            "Must be properties of https://schema.org/Organization or the "
            "selected organization type."
        ),
    )

    # List of text attribute names on this model, in order of preference,
    # for use as the SEO description.
    seo_description_sources = [
        "search_description",  # Comes from wagtail.Page
    ]

    # List of Image object attribute names on this model, in order of
    # preference, for use as the preferred Open Graph / SEO image.
    seo_image_sources = [
        "og_image",
    ]

    # List of text attribute names on this model, in order of preference,
    # for use as the SEO title.
    seo_pagetitle_sources = [
        "seo_title",  # Comes from wagtail.Page
    ]

    @property
    def seo_amp_url(self) -> str:
        """
        Gets the full/absolute/canonical URL for the AMP version of this page.
        """
        return "{0}?amp".format(self.seo_canonical_url)

    @property
    def seo_author(self) -> str:
        """
        Gets the name of the author of this page.
        Override in your Page model as necessary.
        """
        return self.owner.get_full_name()

    @property
    def seo_canonical_url(self) -> str:
        """
        Gets the full/absolute/canonical URL preferred for meta tags and search engines.
        Override in your Page model as necessary.
        """
        return self.get_full_url()

    @property
    def seo_description(self) -> str:
        """
        Gets the correct search engine and Open Graph description of this page.
        Override in your Page model as necessary.
        """
        for attr in self.seo_description_sources:
            if hasattr(self, attr):
                text = getattr(self, attr)
                if text:
                    return text
        return ""

    @property
    def seo_image_url(self) -> str:
        """
        Gets the absolute URL for the primary Open Graph image of this page.
        """
        base_url = utils.get_absolute_media_url(self.get_site())

        for attr in self.seo_image_sources:
            if hasattr(self, attr):
                image = getattr(self, attr)
                if isinstance(image, AbstractImage):
                    return base_url + image.get_rendition("original").url
        return ""

    @property
    def seo_og_type(self) -> str:
        """
        Gets the correct Open Graph type for this page.
        Override in your Page model as necessary.
        """
        return OpenGraphType.WEBSITE.value

    @property
    def seo_sitename(self) -> str:
        """
        Gets the site name.
        Override in your Page model as necessary.
        """
        return self.get_site().site_name

    @property
    def seo_pagetitle(self) -> str:
        """
        Gets the correct search engine and Open Graph title of this page.
        Override in your Page model as necessary.
        """
        for attr in self.seo_pagetitle_sources:
            if hasattr(self, attr):
                text = getattr(self, attr)
                if text:
                    return text

        # Fallback to wagtail.Page.title plus site name.
        return "{0} - {1}".format(self.title, self.seo_sitename)

    @property
    def seo_twitter_card(self) -> str:
        """
        Gets the correct style of twitter card for this page.
        Override in your Page model as necessary.
        """
        return TwitterCard.SUMMARY.value

    seo_meta_panels = [
        MultiFieldPanel(
            [
                FieldPanel("slug"),
                FieldPanel("seo_title"),
                FieldPanel("search_description"),
                ImageChooserPanel("og_image"),
            ],
            _("Search and Social Previews"),
        ),
    ]

    seo_menu_panels = [
        MultiFieldPanel(
            [
                FieldPanel("show_in_menus"),
            ],
            _("Navigation"),
        ),
    ]

    seo_struct_panels = [
        MultiFieldPanel(
            [
                HelpPanel(
                    heading=_("About Organization Structured Data"),
                    content=_(schema.SCHEMA_HELP),
                ),
                FieldPanel("struct_org_type"),
                FieldPanel("struct_org_name"),
                ImageChooserPanel("struct_org_logo"),
                ImageChooserPanel("struct_org_image"),
                FieldPanel("struct_org_phone"),
                FieldPanel("struct_org_address_street"),
                FieldPanel("struct_org_address_locality"),
                FieldPanel("struct_org_address_region"),
                FieldPanel("struct_org_address_postal"),
                FieldPanel("struct_org_address_country"),
                FieldPanel("struct_org_geo_lat"),
                FieldPanel("struct_org_geo_lng"),
                StreamFieldPanel("struct_org_hours"),
                StreamFieldPanel("struct_org_actions"),
                FieldPanel("struct_org_extra_json"),
            ],
            _("Structured Data - Organization"),
        ),
    ]

    seo_panels = seo_meta_panels + seo_menu_panels + seo_struct_panels


@register_setting(icon=SEO_ICON)
class SeoSettings(BaseSetting):
    """
    Toggle Search engine optimization features and meta tags.
    """

    class Meta:
        verbose_name = _("SEO")

    og_meta = models.BooleanField(
        default=True,
        verbose_name=_("Use Open Graph Markup"),
        help_text=_(
            "Show an optimized preview when linking to this site on social media. "
            "See https://ogp.me/"
        ),
    )
    twitter_meta = models.BooleanField(
        default=True,
        verbose_name=_("Use Twitter Markup"),
        help_text=_(
            "Shows content as a card when linking to this site on Twitter. "
            "See https://developer.twitter.com/en/docs/twitter-for-websites/cards"
        ),
    )
    twitter_site = models.CharField(
        max_length=16,
        blank=True,
        verbose_name=_("Twitter Account"),
        help_text=_("The @username of the website owner’s Twitter handle."),
    )
    struct_meta = models.BooleanField(
        default=True,
        verbose_name=_("Use Structured Data"),
        help_text=_(
            "Optimizes information about your organization for search engines. "
            "See https://schema.org/"
        ),
    )
    amp_pages = models.BooleanField(
        default=True,
        verbose_name=_("Use AMP Pages"),
        help_text=_(
            "Generates an alternate AMP version of article pages that are "
            "preferred by search engines. See https://amp.dev/"
        ),
    )

    @property
    def at_twitter_site(self):
        """
        The Twitter site handle, prepended with "@".
        """
        handle = self.twitter_site.lstrip("@")
        return "@{0}".format(handle)

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("amp_pages"),
                FieldPanel("og_meta"),
                FieldPanel("struct_meta"),
                FieldPanel("twitter_meta"),
                FieldPanel("twitter_site"),
            ],
            heading=_("Search Engine Optimization"),
        )
    ]