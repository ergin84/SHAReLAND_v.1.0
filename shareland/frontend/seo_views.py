"""
SEO views for sitemap, robots.txt, and other search engine optimization features
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from django.conf import settings
from .models import Research, Site, ArchaeologicalEvidence
from datetime import datetime


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages"""
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return ['home', 'research-catalog', 'public-research-list']

    def location(self, item):
        return reverse(item)


class ResearchSitemap(Sitemap):
    """Sitemap for research entries"""
    changefreq = "monthly"
    priority = 0.9

    def items(self):
        return Research.objects.all().order_by('-created_date')

    def lastmod(self, obj):
        return obj.created_date

    def location(self, obj):
        return reverse('public-research-detail', args=[obj.pk])


class SiteSitemap(Sitemap):
    """Sitemap for archaeological sites"""
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Site.objects.all()

    def location(self, obj):
        return reverse('site_detail', args=[obj.pk])


@require_GET
def robots_txt(request):
    """
    Generate robots.txt dynamically
    """
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /database-browser/",
        "Disallow: /audit-logs/",
        "Disallow: /api/",
        "Disallow: /ajax/",
        "",
        f"Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml",
        "",
        "# Crawl-delay for good behavior",
        "Crawl-delay: 1",
    ]
    
    return HttpResponse("\n".join(lines), content_type="text/plain")
