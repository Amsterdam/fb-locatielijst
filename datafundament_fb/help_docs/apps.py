from django.apps import AppConfig


class HelpDocsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'help_docs'

    def ready(self):
        import help_docs.signals