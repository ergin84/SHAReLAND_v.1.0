from django.urls import path
from .views import (
    ResearchCreateView,
    ResearchDetailView,
    UserResearchListView,
    ResearchUpdateView,
    ResearchDeleteView,
    SiteCreateView,
    EvidenceCreateView,
    SiteListView,
    SiteDetailView,
    SiteUpdateView,
    SiteDeleteView,
    PublicResearchListView,
    PublicResearchDetailView,
    ResearchCatalogView,
    AuditLogListView,
)
from . import views
from .health_views import health_check, readiness_check, liveness_check

urlpatterns = [
    path('', views.home, name='home'),
    path('public/researches/', PublicResearchListView.as_view(), name='public-research-list'),
    path('public/research-catalog/', ResearchCatalogView.as_view(), name='research-catalog'),
    path('public/research/<int:pk>/', PublicResearchDetailView.as_view(), name='public-research-detail'),
    path('user/<str:username>', UserResearchListView.as_view(), name='user-researches'),
    #path('post/<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('research/<int:pk>/', ResearchDetailView.as_view(), name='research-detail'),
    path('research/new_research/', ResearchCreateView.as_view(), name='create-research'),
    path('research/<int:pk>/update/', ResearchUpdateView.as_view(), name='research-update'),
    path('research/<int:pk>/delete/', ResearchDeleteView.as_view(), name='research-delete'),
    path('api/preview-shapefile/', views.preview_shapefile, name='preview_shapefile'),
    path('site_create/', views.SiteCreateView.as_view(), name='site_create'),
    path('evidence_create/', views.EvidenceCreateView.as_view(), name='evidence_create'),
    path('evidence/<int:pk>/update/', views.EvidenceUpdateView.as_view(), name='evidence_update'),
    path('evidence/<int:pk>/delete/', views.EvidenceDeleteView.as_view(), name='evidence_delete'),
    path('evidence_list/', views.EvidenceListView.as_view(), name='evidence_list'),
    path('evidence/<int:pk>/detail/', views.EvidenceDetailView.as_view(), name='evidence_detail'),
    path('ajax/load-typologies/', views.load_typologies, name='ajax_load_typologies'),
    path('ajax/load-typology-details/', views.load_typology_details, name='ajax_load_typology_details'),
    path('ajax/load-provinces/', views.load_provinces, name='ajax_load_provinces'),
    path('ajax/load-municipalities/', views.load_municipalities, name='ajax_load_municipalities'),
    path('sites/', SiteListView.as_view(), name='site_list'),
    path('site/<int:pk>/', SiteDetailView.as_view(), name='site_detail'),
    path('site/<int:pk>/update/', SiteUpdateView.as_view(), name='site_update'),
    path('site/<int:pk>/delete/', SiteDeleteView.as_view(), name='site_delete'),
    path('ajax/search-authors/', views.search_authors, name='ajax_search_authors'),
    path('ajax/search-users/', views.search_users_autocomplete, name='ajax_search_users'),
    path('database-browser/', views.database_browser, name='database_browser'),
    path('database-export/', views.export_database, name='export_database'),
    path('database-import/', views.import_database, name='import_database'),
    
    # API endpoints for relations
    path('api/sites/', views.api_sites_list, name='api-sites-list'),
    path('api/evidence/', views.api_evidence_list, name='api-evidence-list'),
    path('api/site-research/', views.api_site_research_create, name='api-site-research-create'),
    path('api/site-evidence/', views.api_site_evidence_create, name='api-site-evidence-create'),
    path('api/research-evidence/', views.api_research_evidence_create, name='api-research-evidence-create'),
    path('api/debug/', views.api_debug_data, name='api-debug-data'),
    
    # Health check endpoints
    path('health/', health_check, name='health_check'),
    path('health/ready/', readiness_check, name='readiness_check'),
    path('health/live/', liveness_check, name='liveness_check'),
    
    # Audit logging routes (admin only)
    path('audit-logs/', AuditLogListView.as_view(), name='audit_log_list'),
    path('audit-logs/export/', views.audit_log_export, name='audit_log_export'),
]

