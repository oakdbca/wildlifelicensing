from django.apps import AppConfig


class ApplicationsConfig(AppConfig):
    name = "wildlifelicensing.apps.applications"
    label = "wl_applications"
    verbose_name = "WL Applications"

    run_once = False

    def ready(self):
        if not self.run_once:
            from wildlifelicensing.apps.applications import signals  # noqa

        self.run_once = True
