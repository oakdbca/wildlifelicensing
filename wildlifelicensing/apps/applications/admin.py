from django import forms
from django.contrib import admin
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from reversion.admin import VersionAdmin

from wildlifelicensing.apps.applications.models import Application, ApplicationCondition
from wildlifelicensing.apps.main.models import AssessorGroup, AssessorGroupMembers


class ApplicationAdminForm(forms.ModelForm):
    # data = BetterJSONField()

    class Meta:
        model = Application
        exclude = []


class ApplicationConditionInline(admin.TabularInline):
    model = ApplicationCondition
    extra = 1
    ordering = ("order",)


@admin.register(Application)
class ApplicationAdmin(VersionAdmin):
    date_hierarchy = "lodgement_date"
    list_display = (
        "licence_type",
        "get_user",
        "processing_status",
        "lodgement_number",
        "lodgement_date",
    )
    form = ApplicationAdminForm
    inlines = [
        ApplicationConditionInline,
    ]
    raw_id_fields = (
        "hard_copy",
        "applicant",
        "applicant_profile",
        "proxy_applicant",
        "assigned_officer",
        "previous_application",
        "licence",
    )

    def get_user(self, obj):
        return obj.applicant

    get_user.short_description = "User"
    get_user.admin_order_field = "applicant_profile__user"


class AssessorGroupMembersInline(admin.TabularInline):
    model = AssessorGroupMembers
    extra = 0
    can_delete = False
    raw_id_fields = ("emailuser",)
    verbose_name = "Assessor Group Member"
    verbose_name_plural = "Assessor Group Members"


@admin.register(AssessorGroup)
class AssessorGroupAdmin(admin.ModelAdmin):
    filter_horizontal = ("members",)
    actions = None
    fields = ("name",)
    inlines = [AssessorGroupMembersInline]

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "members":
            kwargs["queryset"] = EmailUser.objects.filter(is_staff=True)
        return super().formfield_for_manytomany(db_field, request, **kwargs)
