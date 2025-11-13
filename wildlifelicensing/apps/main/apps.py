from django.apps import AppConfig


class MainConfig(AppConfig):
    name = "wildlifelicensing.apps.main"
    label = "wl_main"
    verbose_name = "WL Main"

    def ready(self):
        import wildlifelicensing.apps.main.signals  # noqa
        import wildlifelicensing.admin  # noqa - Ensure EmailUserAdmin is registered
