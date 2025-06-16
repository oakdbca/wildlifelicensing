import os
import zlib
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.dispatch import Signal
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from reversion import revisions
from reversion.models import Version

from wildlifelicensing.apps.main.helpers import retrieve_email_user
from wildlifelicensing.apps.main.mixins import MembersPropertiesMixin
from wildlifelicensing.apps.main.oscar_abstract_models import (
    AbstractCountry,
    AbstractUserAddress,
)


class RevisionedMixin(models.Model):
    """
    A model tracked by reversion through the save method.
    """

    def save(self, **kwargs):
        if kwargs.pop("no_revision", False):
            super().save(**kwargs)
        else:
            with revisions.create_revision():
                if "version_user" in kwargs:
                    revisions.set_user(kwargs.pop("version_user", None))
                if "version_comment" in kwargs:
                    revisions.set_comment(kwargs.pop("version_comment", ""))
                super().save(**kwargs)

    @property
    def created_date(self):
        return Version.objects.get_for_object(self).last().revision.date_created

    @property
    def modified_date(self):
        return Version.objects.get_for_object(self).first().revision.date_created

    class Meta:
        abstract = True


class Document(models.Model):
    name = models.CharField(
        max_length=100, blank=True, verbose_name="name", help_text=""
    )
    description = models.TextField(blank=True, verbose_name="description", help_text="")
    file = models.FileField(upload_to="%Y/%m/%d")
    uploaded_date = models.DateTimeField(auto_now_add=True)

    @property
    def path(self):
        return self.file.path

    @property
    def filename(self):
        return os.path.basename(self.path)

    def __str__(self):
        return self.name or self.filename


class BaseAddress(models.Model):
    """Generic address model, intended to provide billing and shipping
    addresses.
    Taken from django-oscar address AbstrastAddress class.
    """

    STATE_CHOICES = (
        ("ACT", "ACT"),
        ("NSW", "NSW"),
        ("NT", "NT"),
        ("QLD", "QLD"),
        ("SA", "SA"),
        ("TAS", "TAS"),
        ("VIC", "VIC"),
        ("WA", "WA"),
    )

    # Addresses consist of 1+ lines, only the first of which is
    # required.
    line1 = models.CharField("Line 1", max_length=255)
    line2 = models.CharField("Line 2", max_length=255, blank=True)
    line3 = models.CharField("Line 3", max_length=255, blank=True)
    locality = models.CharField("Suburb / Town", max_length=255)
    state = models.CharField(max_length=255, default="WA", blank=True)
    country = CountryField(default="AU")
    postcode = models.CharField(max_length=10)
    # A field only used for searching addresses.
    search_text = models.TextField(editable=False)
    hash = models.CharField(max_length=255, db_index=True, editable=False)

    def __str__(self):
        return self.summary

    class Meta:
        abstract = True

    def clean(self):
        # Strip all whitespace
        for field in ["line1", "line2", "line3", "locality", "state"]:
            if self.__dict__[field]:
                self.__dict__[field] = self.__dict__[field].strip()

    def save(self, *args, **kwargs):
        self._update_search_text()
        self.hash = self.generate_hash()
        super().save(*args, **kwargs)

    def _update_search_text(self):
        search_fields = filter(
            bool,
            [
                self.line1,
                self.line2,
                self.line3,
                self.locality,
                self.state,
                str(self.country.name),
                self.postcode,
            ],
        )
        self.search_text = " ".join(search_fields)

    @property
    def summary(self):
        """Returns a single string summary of the address, separating fields
        using commas.
        """
        return ", ".join(self.active_address_fields())

    # Helper methods
    def active_address_fields(self):
        """Return the non-empty components of the address."""
        fields = [
            self.line1,
            self.line2,
            self.line3,
            self.locality,
            self.state,
            self.country,
            self.postcode,
        ]
        fields = [str(f).strip() for f in fields if f]

        return fields

    def join_fields(self, fields, separator=", "):
        """Join a sequence of fields using the specified separator."""
        field_values = []
        for field in fields:
            value = getattr(self, field)
            field_values.append(value)
        return separator.join(filter(bool, field_values))

    def generate_hash(self):
        """
        Returns a hash of the address summary
        """
        return zlib.crc32(self.summary.strip().upper().encode("UTF8"))


class EmailIdentity(models.Model):
    """Table used for matching access email address with EmailUser."""

    user = models.ForeignKey(
        get_user_model(),
        null=True,
        related_name="email_identities",
        on_delete=models.CASCADE,
    )
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.email


class Country(AbstractCountry):
    class Meta:
        abstract = False


class UserAddress(AbstractUserAddress):
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="local_addresses",
        verbose_name=_("User"),
    )

    class Meta:
        abstract = False


class Address(BaseAddress):
    user = models.ForeignKey(
        EmailUser, related_name="wl_profile_addresses", on_delete=models.PROTECT
    )
    oscar_address = models.ForeignKey(
        UserAddress, related_name="wl_profile_addresses", on_delete=models.CASCADE
    )

    class Meta:
        verbose_name_plural = "addresses"
        unique_together = ("user", "hash")


post_clean = Signal()


class Profile(RevisionedMixin):
    user = models.ForeignKey(
        EmailUser,
        verbose_name="User",
        related_name="profiles",
        on_delete=models.PROTECT,
    )
    name = models.CharField(
        "Display Name", max_length=100, help_text="e.g Personal, Work, University, etc"
    )
    email = models.EmailField("Email")
    postal_address = models.ForeignKey(
        Address,
        verbose_name="Postal Address",
        on_delete=models.CASCADE,
        related_name="profiles",
    )
    institution = models.CharField(
        "Institution",
        max_length=200,
        blank=True,
        default="",
        help_text="e.g. Company Name, Tertiary Institution, Government Department, etc",
    )

    @property
    def is_auth_identity(self):
        """
        Return True if the email is an email identity; otherwise return False.
        """
        if not self.email:
            return False

        if not hasattr(self, "_auth_identity"):
            self._auth_identity = EmailIdentity.objects.filter(
                user=self.user, email=self.email
            ).exists()

        return self._auth_identity

    def clean(self):
        super().clean()
        self.email = self.email.lower() if self.email else self.email
        post_clean.send(sender=self.__class__, instance=self)

    def __str__(self):
        if len(self.name) > 0:
            return f"{self.name} ({self.email})"
        else:
            return f"{self.email}"


class Condition(RevisionedMixin):
    text = models.TextField()
    code = models.CharField(max_length=10, unique=True)
    one_off = models.BooleanField(default=False)
    obsolete = models.BooleanField(default=False)

    def __str__(self):
        return self.code


class Region(models.Model):
    name = models.CharField(max_length=200, blank=False, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class WildlifeLicenceCategory(models.Model):
    name = models.CharField(max_length=100, blank=False, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Wildlife licence categories"


class ActiveMixinManager(models.Manager):
    """Manager class for ActiveMixin."""

    def current(self):
        return self.filter(effective_to=None)

    def deleted(self):
        return self.filter(effective_to__isnull=False)


class ActiveMixin(models.Model):
    """Model mixin to allow objects to be saved as 'non-current' or 'inactive',
    instead of deleting those objects.
    The standard model delete() method is overridden.

    "effective_to" is used to flag 'deleted' objects (not null==deleted).
    """

    effective_to = models.DateTimeField(null=True, blank=True)
    objects = ActiveMixinManager()

    class Meta:
        abstract = True

    def is_active(self):
        return self.effective_to is None

    def is_deleted(self):
        return not self.is_active()

    def delete(self, *args, **kwargs):
        """Overide the standard delete method; sets effective_to the current
        date and time.
        """
        if "force" in kwargs and kwargs["force"]:
            kwargs.pop("force", None)
            super().delete(*args, **kwargs)
        else:
            self.effective_to = timezone.now()
            super().save(*args, **kwargs)


class LicenceType(RevisionedMixin, ActiveMixin):
    name = models.CharField(max_length=256)
    short_name = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="The display name that will show in the dashboard",
    )
    version = models.SmallIntegerField(default=1, blank=False, null=False)
    code = models.CharField(max_length=64)
    act = models.CharField(max_length=256, blank=True)
    statement = models.TextField(blank=True)
    authority = models.CharField(max_length=64, blank=True)
    replaced_by = models.ForeignKey(
        "self", on_delete=models.PROTECT, blank=True, null=True
    )
    is_renewable = models.BooleanField(default=True)
    keywords = ArrayField(models.CharField(max_length=50), blank=True, default=list)

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        result = self.short_name or self.name
        if self.replaced_by is None:
            return result
        else:
            return f"{result} (V{self.version})"

    @property
    def is_obsolete(self):
        return self.replaced_by is not None

    class Meta:
        unique_together = ("short_name", "version")


class WildlifeLicenceType(LicenceType):
    product_title = models.CharField(max_length=64, unique=True)
    identification_required = models.BooleanField(default=False)
    senior_applicable = models.BooleanField(default=False)
    default_period = models.PositiveIntegerField(
        "Default Licence Period (days)", blank=True, null=True
    )
    default_conditions = models.ManyToManyField(
        Condition, through="DefaultCondition", blank=True
    )
    application_schema = models.JSONField(blank=True, null=True)
    category = models.ForeignKey(
        WildlifeLicenceCategory, null=True, blank=True, on_delete=models.PROTECT
    )
    variant_group = models.ForeignKey(
        "VariantGroup", null=True, blank=True, on_delete=models.CASCADE
    )
    help_text = models.TextField(blank=True)

    def clean(self):
        """
        Pre save validation:
        - A payment product and all its variants must exist before creating a LicenceType.
        - Check for senior voucher if applicable.
        :return: raise an exception if error
        """
        from wildlifelicensing.apps.payments import utils as payment_utils

        variant_codes = payment_utils.generate_product_title_variants(self)

        missing_product_variants = []

        for variant_code in variant_codes:
            if payment_utils.get_product(variant_code) is None:
                missing_product_variants.append(variant_code)

        if missing_product_variants:
            msg = mark_safe(
                "The payments products with titles matching the below list of product codes were not "
                "found. Note: You must create a payment product(s) for a new licence type and all its "
                "variants, even if the licence has no fee. <ul><li>{}</li></ul>".format(
                    "</li><li>".join(missing_product_variants)
                )
            )

            raise ValidationError(msg)


class Licence(RevisionedMixin, ActiveMixin):
    holder = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="holder"
    )
    issuer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="issuer",
        blank=True,
        null=True,
    )
    licence_type = models.ForeignKey(LicenceType, on_delete=models.PROTECT)
    licence_number = models.CharField(max_length=64, blank=True, null=True)
    licence_sequence = models.IntegerField(blank=True, default=0)
    issue_date = models.DateField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    is_renewable = models.BooleanField(blank=True, null=True)

    class Meta:
        unique_together = ("licence_number", "licence_sequence")

    def __str__(self):
        return f"{self.licence_type} {self.licence_number}-{self.licence_sequence}"


class WildlifeLicence(Licence):
    MONTH_FREQUENCY_CHOICES = [
        (-1, "One off"),
        (1, "Monthly"),
        (3, "Quarterly"),
        (6, "Twice-Yearly"),
        (12, "Yearly"),
    ]
    DEFAULT_FREQUENCY = MONTH_FREQUENCY_CHOICES[0][0]

    profile = models.ForeignKey(Profile, on_delete=models.PROTECT)
    purpose = models.TextField(blank=True)
    locations = models.TextField(blank=True)
    cover_letter_message = models.TextField(blank=True)
    additional_information = models.TextField(blank=True)
    licence_document = models.ForeignKey(
        Document,
        blank=True,
        null=True,
        related_name="licence_document",
        on_delete=models.PROTECT,
    )
    cover_letter_document = models.ForeignKey(
        Document,
        blank=True,
        null=True,
        related_name="cover_letter_document",
        on_delete=models.PROTECT,
    )
    return_frequency = models.IntegerField(
        choices=MONTH_FREQUENCY_CHOICES, default=DEFAULT_FREQUENCY
    )
    replaced_by = models.ForeignKey(
        "self", blank=True, null=True, on_delete=models.PROTECT
    )
    regions = models.ManyToManyField(Region, blank=False)
    variants = models.ManyToManyField(
        "Variant", blank=True, through="WildlifeLicenceVariantLink"
    )
    renewal_sent = models.BooleanField(default=False)
    extracted_fields = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.reference

    def get_title_with_variants(self):
        if self.pk is not None and self.variants.exists():
            return "{} ({})".format(
                self.licence_type.name,
                " / ".join(self.variants.all().values_list("name", flat=True)),
            )
        else:
            return self.licence_type.name

    @property
    def reference(self):
        return f"{self.licence_number}-{self.licence_sequence}"

    @property
    def is_issued(self):
        return self.licence_number is not None and len(self.licence_number) > 0

    def search_extracted_fields(self, search):
        extracted_fields = self.extracted_fields

        if search == "":
            return ""

        authorised_persons = []
        all_species = []
        # information extracted from application
        if extracted_fields:
            for field in extracted_fields:
                if "children" in field and field["type"] == "group":
                    if search in field["name"]:
                        if search == "authorised_persons":
                            authorised_person = {"given_names": "", "surname": ""}
                            for index, group in enumerate(field["children"]):
                                for child_field in group:
                                    # Get surname
                                    if (
                                        "surname" in child_field["name"]
                                        and "data" in child_field
                                        and child_field["data"]
                                    ):
                                        authorised_person["surname"] = child_field[
                                            "data"
                                        ]
                                    elif (
                                        "given_names" in child_field["name"]
                                        and "data" in child_field
                                        and child_field["data"]
                                    ):
                                        authorised_person["given_names"] = child_field[
                                            "data"
                                        ]
                                name = "{} {}".format(
                                    authorised_person["surname"],
                                    authorised_person["given_names"],
                                )
                                authorised_persons.append(name)
                        elif search == "species_estimated_number":
                            species = {"name": "", "number": ""}
                            for index, group in enumerate(field["children"]):
                                for child_field in group:
                                    # Get surname
                                    if (
                                        "species_causing_damage" in child_field["name"]
                                        and "data" in child_field
                                        and child_field["data"]
                                    ):
                                        species["name"] = child_field["data"]
                                    elif (
                                        "number_causing_damage" in child_field["name"]
                                        and "data" in child_field
                                        and child_field["data"]
                                    ):
                                        species["number"] = child_field["data"]
                                name = "{} : {}".format(
                                    species["name"], species["number"]
                                )
                                all_species.append(name)

        if search == "authorised_persons":
            return authorised_persons
        elif search == "species_estimated_number":
            return all_species
        else:
            return ""


class DefaultCondition(models.Model):
    condition = models.ForeignKey(Condition, on_delete=models.CASCADE)
    wildlife_licence_type = models.ForeignKey(
        WildlifeLicenceType, on_delete=models.CASCADE
    )
    order = models.IntegerField()

    class Meta:
        unique_together = ("condition", "wildlife_licence_type", "order")


class CommunicationsLogEntry(models.Model):
    TYPE_CHOICES = [
        ("email", "Email"),
        ("phone", "Phone Call"),
        ("main", "Mail"),
        ("person", "In Person"),
    ]
    DEFAULT_TYPE = TYPE_CHOICES[0][0]

    to = models.CharField(max_length=200, blank=True, verbose_name="To")
    fromm = models.CharField(max_length=200, blank=True, verbose_name="From")
    cc = models.CharField(max_length=200, blank=True, verbose_name="cc")

    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=DEFAULT_TYPE)
    reference = models.CharField(max_length=100, blank=True)
    subject = models.CharField(
        max_length=200, blank=True, verbose_name="Subject / Description"
    )
    text = models.TextField(blank=True)
    documents = models.ManyToManyField(Document, blank=True)

    customer = models.ForeignKey(
        EmailUser, null=True, related_name="customer", on_delete=models.PROTECT
    )
    staff = models.ForeignKey(
        EmailUser, null=True, related_name="staff", on_delete=models.PROTECT
    )

    created = models.DateTimeField(auto_now_add=True, null=False, blank=False)


class Variant(models.Model):
    name = models.CharField(max_length=200)
    product_title = models.CharField(max_length=64, unique=True)
    help_text = models.TextField(blank=True)

    def __str__(self):
        return self.name


class VariantGroup(models.Model):
    name = models.CharField(max_length=50)
    child = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE)
    variants = models.ManyToManyField(Variant)

    def clean(self):
        """
        Guards against putting itself as child
        :return:
        """
        if self.child and self.child.pk == self.pk:
            raise ValidationError("Can't put yourself as a child")

    def __str__(self):
        if self.child is None or self.child.pk == self.pk:
            return self.name
        else:
            return f"{self.name} > {self.child.__str__()}"


class WildlifeLicenceVariantLink(models.Model):
    licence = models.ForeignKey(WildlifeLicence, on_delete=models.CASCADE)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    order = models.IntegerField()


class AssessorGroup(models.Model, MembersPropertiesMixin):
    name = models.CharField(max_length=50)
    email = models.EmailField()
    members = models.ManyToManyField(EmailUser, blank=True)
    purpose = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class UserAction(models.Model):
    who = models.ForeignKey(
        EmailUser, null=False, blank=False, on_delete=models.PROTECT
    )
    when = models.DateTimeField(null=False, blank=False, auto_now_add=True)
    what = models.TextField(blank=False)

    def __str__(self):
        return "{what} ({who} at {when})".format(
            what=self.what, who=self.who, when=self.when
        )

    class Meta:
        abstract = True


def m2m_field_through_model_factory(model_name, m2m_field_name="members"):
    """Returns a through model for a m2m field (e.g. members) that mirrors
    the existing django-managed through table of the m2m field"""

    class MembersThroughModel(models.Model):
        class Meta:
            app_label = "wl_main"
            # Mirror the existing django-managed through table of the m2m field
            db_table = f"wl_main_{model_name.lower()}_{m2m_field_name}"
            abstract = True
            managed = False
            unique_together = (f"{model_name.lower()}", "emailuser")

        @property
        def emailuser_object(self):
            return retrieve_email_user(self.emailuser_id)

    # Fk to model instance
    MembersThroughModel.add_to_class(
        f"{model_name.lower()}",
        models.ForeignKey(
            f"{model_name}",
            on_delete=models.PROTECT,
            related_name=f"{model_name.lower()}_{m2m_field_name}",
        ),
    )
    # Fk to EmailUserRO
    MembersThroughModel.add_to_class(
        "emailuser",
        models.ForeignKey(
            EmailUser,
            on_delete=models.PROTECT,
            related_name=f"{model_name.lower()}_{m2m_field_name}",
        ),
    )
    return MembersThroughModel


class AssessorGroupMembers(m2m_field_through_model_factory("AssessorGroup")):
    pass

    class Meta:
        abstract = False


class Product(models.Model):
    title = models.CharField(max_length=200, unique=True)
    partner_sku = models.CharField(max_length=200, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    oracle_code = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        default=settings.DEFAULT_ORACLE_CODE,
    )
    is_discountable = models.BooleanField(
        _("Is discountable?"),
        default=True,
        help_text=_(
            "This flag indicates if the user can have a seniors discount on this product"
        ),
    )

    def __str__(self):
        return self.title

    @property
    def free_of_charge(self):
        return self.price == Decimal("0.00")


class NomosTaxonomy(models.Model):
    # This will include the canoncial name and any vernacular names in brackets
    name = models.CharField(max_length=250, unique=True, null=False, blank=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "NOMOS Taxonomies"
