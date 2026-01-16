"""
SEO utilities and context processors for improved search engine visibility
"""
from django.conf import settings


class SEOMetaTags:
    """
    Class to manage SEO meta tags for different pages
    """
    def __init__(self, title=None, description=None, keywords=None, 
                 image=None, url=None, article_published_time=None, 
                 article_modified_time=None, article_author=None):
        self.title = title or "SHAReLAND - Archaeological Research Database"
        self.description = description or "SHAReLAND is a comprehensive database for archaeological research, sites, and evidence. Explore archaeological findings and research data."
        self.keywords = keywords or "archaeology, archaeological research, archaeological sites, archaeological evidence, research database, open landscapes"
        self.image = image or f"{settings.STATIC_URL}frontend/logo-social.png"
        self.url = url or ""
        self.article_published_time = article_published_time
        self.article_modified_time = article_modified_time
        self.article_author = article_author
    
    def get_context(self):
        """Return context dictionary for templates"""
        return {
            'seo_title': self.title,
            'seo_description': self.description,
            'seo_keywords': self.keywords,
            'seo_image': self.image,
            'seo_url': self.url,
            'seo_article_published_time': self.article_published_time,
            'seo_article_modified_time': self.article_modified_time,
            'seo_article_author': self.article_author,
        }


def seo_context_processor(request):
    """
    Context processor to add default SEO values to all templates
    """
    return {
        'site_name': 'SHAReLAND',
        'site_tagline': 'Archaeological Research Database',
        'default_seo_title': 'SHAReLAND - Archaeological Research Database',
        'default_seo_description': 'Comprehensive database for archaeological research, sites, and evidence. Explore archaeological findings and research data.',
    }
