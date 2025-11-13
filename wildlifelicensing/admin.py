from django.contrib.admin import AdminSite
from django.contrib.gis import admin

from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from ledger_api_client.managed_models import SystemGroupPermission

class WildlifeLicensingAdminSite(AdminSite):
    site_header = "Wildlife Licensing Administration"
    site_title = "Wildlife Licensing"


wildlife_licensing_admin_site = WildlifeLicensingAdminSite(
    name="wildlifelicensingadmin"
)

admin.site.index_template = "admin-index.html"

# Unregister EmailUser if already registered by ledger_api_client
if EmailUser in admin.site._registry:
    admin.site.unregister(EmailUser)

@admin.register(EmailUser)
class EmailUserAdmin(admin.ModelAdmin):
    list_display = (
        "ledger_id",
        "email",
        "first_name",
        "last_name",
        "groups",
        "is_staff",
        "is_active",
        "is_superuser",
    )
    fields = (
        "ledger_id",
        "email",
        "first_name",
        "last_name",
        "groups",
        "is_staff",
        "is_active",
        "is_superuser",
    )
    ordering = ("email",)
    search_fields = ("id", "email", "first_name", "last_name")

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.opts.verbose_name_plural = "Email Users (Read-Only)"

    def has_change_permission(self, request, obj=None):
        if obj is None:  # and obj.status > 1:
            return True
        return None

    def has_delete_permission(self, request, obj=None):
        return None

    def groups(self, obj):
        groups = SystemGroupPermission.objects.filter(emailuser=obj)
        return ", ".join([group.system_group.name for group in groups])

    def ledger_id(self, obj):
        return obj.id

    ledger_id.short_description = "Ledger ID"
