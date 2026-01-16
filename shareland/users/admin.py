from django.contrib import admin
from django.contrib.auth.models import User

from .models import Profile, UserRole


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['role', 'is_active', 'description']
    list_filter = ['is_active']
    search_fields = ['role', 'description']
    fieldsets = (
        ('Role', {'fields': ('role', 'is_active')}),
        ('Details', {'fields': ('description', 'permissions')}),
    )
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'affiliation', 'orcid', 'get_roles']
    list_filter = ['affiliation', 'user_roles']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'affiliation', 'orcid', 'contact_email']
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Professional Information', {'fields': ('affiliation', 'orcid', 'contact_email')}),
        ('Personal Information', {'fields': ('birth_date', 'qualification')}),
        ('Roles & Permissions', {'fields': ('user_roles',)}),
        ('Profile Image', {'fields': ('image',)}),
        ('Legacy', {'fields': ('id_anagraphic',)}),
    )
    filter_horizontal = ['user_roles']
    
    def get_roles(self, obj):
        """Display roles as comma-separated string"""
        return ', '.join(obj.get_role_names()) or '—'
    get_roles.short_description = 'Roles'

