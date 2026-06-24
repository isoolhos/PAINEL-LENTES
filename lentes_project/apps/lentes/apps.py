from django.apps import AppConfig


class LentesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.lentes"
    verbose_name = "Painel de Lentes"

    def ready(self):
        from django.contrib import admin

        admin.site.site_header = "Painel Lentes OPS"
        admin.site.site_title = "Painel Lentes OPS"
        admin.site.index_title = "Administracao do Painel Lentes OPS"
