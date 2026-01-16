from django.contrib import admin
from .audit_models import AuditLog, AccessLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'operation', 'model_name', 'object_id', 'ip_address')
    list_filter = ('operation', 'model_name', 'timestamp', 'user')
    search_fields = ('user__username', 'model_name', 'object_id', 'object_str')
    readonly_fields = ('timestamp', 'user', 'operation', 'model_name', 'object_id', 'object_str', 'changes', 'old_values', 'new_values', 'ip_address', 'user_agent')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'page', 'ip_address')
    list_filter = ('timestamp', 'user')
    search_fields = ('user__username', 'page', 'view_name')
    readonly_fields = ('timestamp', 'user', 'page', 'view_name', 'ip_address')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

