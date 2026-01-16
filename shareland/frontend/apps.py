from django.apps import AppConfig


class FrontendConfig(AppConfig):
    name = 'frontend'
    
    def ready(self):
        # Import audit logging signals
        import frontend.audit_middleware

