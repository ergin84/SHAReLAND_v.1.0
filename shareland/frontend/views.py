import csv
import json
import logging
import os
import subprocess
from collections import defaultdict
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.db import connection, models
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .audit_models import AuditLog
from .forms import ArchaeologicalEvidenceForm, ResearchForm, SiteForm
from .models import SiteSettings
from .models import (
    ArchEvBiblio,
    ArchEvRelatedDoc,
    ArchEvResearch,
    ArchEvSources,
    ArchaeologicalEvidence,
    Bibliography,
    Chronology,
    Image,
    ImageScale,
    ImageType,
    Interpretation,
    Investigation,
    Municipality,
    Province,
    Research,
    ResearchAuthor,
    Site,
    SiteArchEvidence,
    SiteBibliography,
    SiteInvestigation,
    SiteRelatedDocumentation,
    SiteResearch,
    SiteSources,
    SiteToponymy,
    Sources,
    SourcesType,
    Typology,
    TypologyDetail,
)
from .shapefile_utils import extract_geometry_from_shapefile
from .utils import create_folium_map, parse_geometry_string
from .utils.author_user import find_or_create_user_as_author, get_or_update_user_profile

logger = logging.getLogger(__name__)



def save_uploaded_image(image_file, subfolder='images'):
    """
    Save uploaded image file to media folder and return the accessible URL path.
    Returns: /media/images/filename.ext or None if save fails
    """
    if not image_file:
        return None

    try:
        # Sanitize filename - keep only alphanumeric, dots, hyphens, underscores
        filename = image_file.name
        filename = "".join(c for c in filename if c.isalnum() or c in '._-')

        if not filename:
            return None

        # Create subdirectory path
        media_path = f'{subfolder}/{filename}'

        # Save file to media folder
        file_path = default_storage.save(media_path, image_file)

        # Return accessible URL path
        return f'/media/{file_path}'
    except Exception as e:
        print(f"Error saving image: {e}")
        return None


def _parse_team_members(text):
    """Parse 'Name | Role' multiline text into list of dicts with initials."""
    members = []
    for line in (text or '').splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split('|', 1)
        name = parts[0].strip()
        role = parts[1].strip() if len(parts) > 1 else ''
        # Build initials from first two words
        words = name.split()
        initials = ''.join(w[0].upper() for w in words[:2]) if words else '?'
        members.append({'name': name, 'role': role, 'initials': initials})
    return members


def home(request):
    """Home page with statistics and project information."""
    total_research = Research.objects.count()
    total_sites = Site.objects.count()
    total_evidence = ArchaeologicalEvidence.objects.count()
    total_users = User.objects.filter(is_active=True).count()

    site_cfg = SiteSettings.load()

    # ── Key Information: resolve values with Python fallbacks ──
    ki_date        = (site_cfg.project_date     if site_cfg and site_cfg.project_date     else '2024 \u2013 ongoing')
    ki_institution = (site_cfg.institution_name if site_cfg and site_cfg.institution_name else 'Università degli Studi Roma Tre')
    ki_dept        = (site_cfg.institution_dept if site_cfg and site_cfg.institution_dept else 'Dipartimento di Studi Umanistici')
    ki_lab         = (site_cfg.lab_name         if site_cfg and site_cfg.lab_name         else 'Archeopaesaggi Roma Tre')
    ki_instagram   = (site_cfg.lab_instagram    if site_cfg and site_cfg.lab_instagram    else 'archeopaesaggi_roma3')
    ki_phd_title   = (site_cfg.phd_title        if site_cfg and site_cfg.phd_title        else 'Shared Archaeological Landscapes / Paesaggi Archeologici Condivisi')
    ki_phd_person  = (site_cfg.phd_researcher   if site_cfg and site_cfg.phd_researcher   else 'Margherita Bottoni')
    ki_phd_years   = (site_cfg.phd_years        if site_cfg and site_cfg.phd_years        else '2024\u20132027')

    # ── Team: parse 'Name | Role' lines ────────────────────────
    team_coordinators = _parse_team_members(site_cfg.team_coordinators if site_cfg else '')
    team_technical    = _parse_team_members(site_cfg.team_technical    if site_cfg else '')

    if not team_coordinators:
        team_coordinators = [
            {'name': 'Emanuele Farinetti', 'role': 'Project Coordinator \u2014 Università Roma Tre', 'initials': 'EF'},
            {'name': 'Margherita Bottoni', 'role': 'Project Coordinator & PhD Researcher',            'initials': 'MB'},
        ]
    if not team_technical:
        team_technical = [
            {'name': 'Emanuele Bellini', 'role': 'Technical Developer', 'initials': 'EB'},
            {'name': 'Ergin Mehmeti',    'role': 'Technical Developer', 'initials': 'EM'},
        ]

    context = {
        'total_research': total_research,
        'total_sites': total_sites,
        'total_evidence': total_evidence,
        'total_users': total_users,
        # Key info
        'ki_date':       ki_date,
        'ki_institution': ki_institution,
        'ki_dept':        ki_dept,
        'ki_lab':         ki_lab,
        'ki_instagram':   ki_instagram,
        'ki_phd_title':   ki_phd_title,
        'ki_phd_person':  ki_phd_person,
        'ki_phd_years':   ki_phd_years,
        # Team
        'team_coordinators': team_coordinators,
        'team_technical':    team_technical,
    }
    return render(request, 'frontend/home.html', context)


def getfile(request):
    from django.contrib.staticfiles.views import serve
    return serve(request, 'File')


class ResearchListView(LoginRequiredMixin, ListView):
    model = Research
    template_name = 'frontend/research_list.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'researches'
    ordering = ['-year']
    paginate_by = 5

    def get_queryset(self):
        return Research.objects.all().order_by('-year')


class PublicResearchListView(ListView):
    """
    Public view (no authentication required) to display all research with related sites and evidence
    """
    model = Research
    template_name = 'frontend/public_research_list.html'
    context_object_name = 'researches'
    ordering = ['-year']
    paginate_by = 10

    def get_queryset(self):
        return Research.objects.all().order_by('-year')


class PublicResearchDetailView(DetailView):
    """
    Public view (no authentication required) to display research details with all related sites and evidence
    """
    model = Research
    template_name = 'frontend/public_research_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        research = self.object

        # Get unique sites related to this research (avoid duplicates from multiple links)
        site_ids = (
            SiteResearch.objects
            .filter(id_research=research)
            .values_list('id_site_id', flat=True)
            .distinct()
        )
        sites = Site.objects.filter(id__in=site_ids)

        # Get all archaeological evidence related to this research (directly)
        # Use values_list to get IDs first, then fetch objects to avoid geometry comparison
        direct_evidence_ids = ArchEvResearch.objects.filter(
            id_research=research.id
        ).values_list('id_archaeological_evidence_id', flat=True)
        ArchaeologicalEvidence.objects.filter(id__in=direct_evidence_ids)

        # Get archaeological evidence linked through sites
        site_evidence_ids = SiteArchEvidence.objects.filter(
            id_site_id__in=site_ids
        ).values_list('id_archaeological_evidence_id', flat=True)
        ArchaeologicalEvidence.objects.filter(id__in=site_evidence_ids)

        # Combine all evidence IDs and fetch unique objects
        all_evidence_ids = set(list(direct_evidence_ids) + list(site_evidence_ids))
        all_evidences = ArchaeologicalEvidence.objects.filter(id__in=all_evidence_ids)

        # Get authors for this research
        author_ids = list(
            ResearchAuthor.objects
            .filter(id_research=research)
            .values_list('id_author_id', flat=True)
            .distinct()
        )
        authors = User.objects.filter(id__in=author_ids).order_by('last_name', 'first_name', 'email').select_related('profile')

        # For each site, get its related data
        sites_with_details = []
        for site in sites:
            # Get evidence IDs for this site (avoid distinct on geometry)
            site_evidence_ids_list = SiteArchEvidence.objects.filter(
                id_site_id=site.id
            ).values_list('id_archaeological_evidence_id', flat=True)
            site_evidences_list = ArchaeologicalEvidence.objects.filter(id__in=site_evidence_ids_list)

            site_data = {
                'site': site,
                'toponymy': SiteToponymy.objects.filter(id_site=site).first(),
                'interpretation': Interpretation.objects.filter(id_site=site).first(),
                'investigation': SiteInvestigation.objects.filter(id_site=site).select_related('id_investigation').first(),
                'bibliography': SiteBibliography.objects.filter(id_site=site).select_related('id_bibliography').first(),
                'sources': SiteSources.objects.filter(id_site=site).select_related('id_sources').first(),
                'related_doc': SiteRelatedDocumentation.objects.filter(id_site=site).first(),
                'images': Image.objects.filter(id_site=site).select_related('id_image_type', 'id_image_scale'),
                'evidences': site_evidences_list,
            }
            sites_with_details.append(site_data)

        # For each evidence, get its related data
        evidences_with_details = []
        for evidence in all_evidences:
            evidence_data = {
                'evidence': evidence,
                'bibliography': ArchEvBiblio.objects.filter(id_archaeological_evidence=evidence).select_related('id_bibliography').first(),
                'sources': ArchEvSources.objects.filter(id_archaeological_evidence=evidence).select_related('id_sources').first(),
                'related_doc': ArchEvRelatedDoc.objects.filter(id_archaeological_evidence=evidence).first(),
            }
            evidences_with_details.append(evidence_data)

        # Create Folium map for research geometry
        map_html = None
        if research.geometry:
            map_html = create_folium_map(
                research.geometry,
                research_title=research.title or "Research Area"
            )

        # Add user and research info for permission checks in template
        context.update({
            'sites_with_details': sites_with_details,
            'evidences_with_details': evidences_with_details,
            'authors': authors,
            'map_html': map_html,
            'research_owner': research.submitted_by if research.submitted_by else None,
        })
        return context


class ResearchCatalogView(ListView):
    """Public catalog page with research → site → evidence tree."""
    model = Research
    template_name = 'frontend/research_catalog.html'
    context_object_name = 'researches'
    paginate_by = 5

    def get_queryset(self):
        queryset = Research.objects.all().select_related('submitted_by').order_by('title')
        search_query = self.request.GET.get('q', '').strip()

        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(abstract__icontains=search_query) |
                Q(keywords__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        researches = list(context.get('researches', []))
        search_query = self.request.GET.get('q', '').strip()
        context['search_query'] = search_query

        if not researches:
            context['catalog_entries'] = []
            context['map_data_json'] = []
            return context

        research_ids = [research.id for research in researches]

        # Batch-load research authors (avoids N+1)
        def _display_name(user):
            try:
                return user.profile.get_display_name()
            except Exception:
                return user.get_full_name() or user.username

        author_links = ResearchAuthor.objects.filter(
            id_research_id__in=research_ids
        ).select_related('id_author', 'id_author__profile')
        authors_by_research = defaultdict(list)
        for link in author_links:
            if link.id_author:
                authors_by_research[link.id_research_id].append(
                    _display_name(link.id_author)
                )

        site_links = SiteResearch.objects.filter(
            id_research_id__in=research_ids
        ).select_related('id_site')
        site_ids = [link.id_site_id for link in site_links]

        sites = Site.objects.filter(id__in=site_ids).select_related(
            'id_country', 'id_region', 'id_province', 'id_municipality'
        )
        site_by_id = {site.id: site for site in sites}

        site_map = defaultdict(list)
        for link in site_links:
            site = site_by_id.get(link.id_site_id)
            if site:
                site_map[link.id_research_id].append(site)

        site_evidence_links = SiteArchEvidence.objects.filter(
            id_site_id__in=site_ids
        ).select_related('id_archaeological_evidence')
        site_evidence_map = defaultdict(list)
        for relation in site_evidence_links:
            evidence = relation.id_archaeological_evidence
            if evidence:
                site_evidence_map[relation.id_site_id].append(evidence)

        direct_evidence_links = ArchEvResearch.objects.filter(
            id_research__in=research_ids
        ).select_related('id_archaeological_evidence')
        direct_evidence_map = defaultdict(list)
        for relation in direct_evidence_links:
            evidence = relation.id_archaeological_evidence
            if evidence:
                direct_evidence_map[relation.id_research].append(evidence)

        catalog_entries = []
        map_data = []
        for research in researches:
            sites_payload = []
            site_markers = []
            evidence_markers = []

            def _to_float(value):
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return None

            for site in site_map.get(research.id, []):
                sites_payload.append({
                    'site': site,
                    'evidences': site_evidence_map.get(site.id, []),
                })

                # Site marker
                lat = _to_float(site.lat)
                lon = _to_float(site.lon)
                if lat is not None and lon is not None:
                    site_markers.append({
                        'id': site.id,
                        'name': site.site_name or f"Site #{site.id}",
                        'lat': lat,
                        'lon': lon,
                        'region': getattr(site.id_region, 'denominazione_regione', None),
                        'municipality': getattr(site.id_municipality, 'denominazione_comune', None),
                    })

                # Evidences linked to this site
                for ev in site_evidence_map.get(site.id, []):
                    ev_lat = _to_float(getattr(ev, 'lat', None))
                    ev_lon = _to_float(getattr(ev, 'lon', None))
                    if ev_lat is not None and ev_lon is not None:
                        evidence_markers.append({
                            'id': ev.id,
                            'name': ev.evidence_name or f"Evidence #{ev.id}",
                            'lat': ev_lat,
                            'lon': ev_lon,
                            'site_id': site.id,
                            'region': getattr(ev.id_region, 'denominazione_regione', None),
                            'municipality': getattr(ev.id_municipality, 'denominazione_comune', None),
                        })

            catalog_entries.append({
                'research': research,
                'sites': sites_payload,
                'direct_evidences': direct_evidence_map.get(research.id, []),
                'author_names': authors_by_research.get(research.id, []),
            })

            # Direct evidences linked to research (without a site)
            for ev in direct_evidence_map.get(research.id, []):
                ev_lat = _to_float(getattr(ev, 'lat', None))
                ev_lon = _to_float(getattr(ev, 'lon', None))
                if ev_lat is not None and ev_lon is not None:
                    evidence_markers.append({
                        'id': ev.id,
                        'name': ev.evidence_name or f"Evidence #{ev.id}",
                        'lat': ev_lat,
                        'lon': ev_lon,
                        'region': getattr(ev.id_region, 'denominazione_regione', None),
                        'municipality': getattr(ev.id_municipality, 'denominazione_comune', None),
                    })

            research_polygon = parse_geometry_string(research.geometry) if getattr(research, 'geometry', None) else None
            map_data.append({
                'id': research.id,
                'title': research.title or f"Research #{research.id}",
                'year': research.year,
                'type': research.type,
                'abstract': (research.abstract or '')[:200],
                'geometry': research_polygon,
                'sites': site_markers,
                'evidences': evidence_markers,
            })

        context['catalog_entries'] = catalog_entries
        context['map_data_json'] = map_data
        return context


class UserResearchListView(LoginRequiredMixin, ListView):
    model = Research
    template_name = 'frontend/user_research.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'researches'
    paginate_by = 5

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return Research.objects.filter(submitted_by=user).order_by('-year')


class ResearchCreateView(LoginRequiredMixin, CreateView):
    model = Research
    form_class = ResearchForm
    template_name = 'frontend/research_form.html'

    def form_valid(self, form):
        form.instance.submitted_by = self.request.user

        # === Handle main author ===
        is_self_author = self.request.POST.get('is_self_author')
        if is_self_author == 'yes':
            # User is the main author
            author_user = self.request.user
        else:
            # Search for user or create new one
            user_id = self.request.POST.get('author_user_id')

            if user_id:
                author_user = get_object_or_404(User, pk=user_id)
                affiliation = self.request.POST.get('author_affiliation', '')
                orcid = self.request.POST.get('author_orcid', '')
                author_user = get_or_update_user_profile(author_user, affiliation=affiliation, orcid=orcid)
            else:
                author_name = self.request.POST.get('author_name')
                author_surname = self.request.POST.get('author_surname')
                author_email = self.request.POST.get('author_email')
                affiliation = self.request.POST.get('author_affiliation', '')
                orcid = self.request.POST.get('author_orcid', '')

                if not author_name or not author_surname or not author_email:
                    form.add_error(None, 'Name, surname, and email are required for new author')
                    return self.form_invalid(form)

                author_user = find_or_create_user_as_author(
                    author_name, author_surname, author_email,
                    affiliation=affiliation, orcid=orcid
                )

        # Note: Research model uses ResearchAuthor junction table for authors,
        # not a direct author field

        # === Handle shapefile → geometry ===
        shapefile = self.request.FILES.get('shapefile')
        if shapefile:
            try:
                geometry = extract_geometry_from_shapefile(shapefile)
                form.instance.geometry = geometry
            except ValidationError as e:
                form.add_error('shapefile', e)
                return self.form_invalid(form)

        # === Save research ===
        self.object = form.save()

        # === Add to ResearchAuthor table (using get_or_create to avoid duplicates) ===
        ResearchAuthor.objects.get_or_create(id_research=self.object, id_author=author_user)

        # === Handle co-authors ===
        index = 0
        while True:
            co_user_id = self.request.POST.get(f'coauthor_user_id_{index}')

            if co_user_id:
                # User found
                co_user = User.objects.filter(pk=co_user_id).first()
                if co_user:
                    co_affiliation = self.request.POST.get(f'coauthor_affiliation_{index}', '')
                    co_orcid = self.request.POST.get(f'coauthor_orcid_{index}', '')
                    co_user = get_or_update_user_profile(co_user, affiliation=co_affiliation, orcid=co_orcid)
                    ResearchAuthor.objects.get_or_create(id_research=self.object, id_author=co_user)
            else:
                name = self.request.POST.get(f'coauthor_name_{index}')
                surname = self.request.POST.get(f'coauthor_surname_{index}')
                email = self.request.POST.get(f'coauthor_email_{index}')

                if name and surname and email:
                    co_affiliation = self.request.POST.get(f'coauthor_affiliation_{index}', '')
                    co_orcid = self.request.POST.get(f'coauthor_orcid_{index}', '')
                    co_user = find_or_create_user_as_author(
                        name, surname, email,
                        affiliation=co_affiliation, orcid=co_orcid
                    )
                    ResearchAuthor.objects.get_or_create(id_research=self.object, id_author=co_user)
                else:
                    break
            index += 1

        return render(self.request, 'frontend/research_success.html', {'research': self.object})


class ResearchDetailView(LoginRequiredMixin, DetailView):
    model = Research
    template_name = 'frontend/research_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        research = self.object

        # Get unique sites linked to this research (avoid duplicates)
        site_ids = SiteResearch.objects.filter(id_research=research).values_list('id_site_id', flat=True).distinct()
        unique_sites = Site.objects.filter(id__in=site_ids)

        # Get authors for this research (distinct to avoid duplicates)
        author_ids = ResearchAuthor.objects.filter(id_research=research).values_list('id_author_id', flat=True).distinct()
        authors = User.objects.filter(id__in=author_ids).select_related('profile')

        # For each site, get its related data (similar to public view)
        sites_with_details = []
        for site in unique_sites:
            # Get evidence IDs for this site
            site_evidence_ids_list = SiteArchEvidence.objects.filter(
                id_site_id=site.id
            ).values_list('id_archaeological_evidence_id', flat=True)
            site_evidences_list = ArchaeologicalEvidence.objects.filter(id__in=site_evidence_ids_list)

            # Get ALL bibliographies for this site (not just first)
            site_biblios = SiteBibliography.objects.filter(id_site=site).select_related('id_bibliography')
            bibliographies = [sb.id_bibliography for sb in site_biblios]

            # Get ALL sources for this site
            site_sources_links = SiteSources.objects.filter(id_site=site).select_related('id_sources')
            sources = [ss.id_sources for ss in site_sources_links]

            # Get ALL related docs for this site
            related_docs = SiteRelatedDocumentation.objects.filter(id_site=site)

            # Get ALL images for this site
            site_images = Image.objects.filter(id_site=site)

            site_data = {
                'site': site,
                'toponymy': SiteToponymy.objects.filter(id_site=site).first(),
                'interpretation': Interpretation.objects.filter(id_site=site).first(),
                'investigation': SiteInvestigation.objects.filter(id_site=site).select_related('id_investigation').first(),
                'bibliographies': bibliographies,  # Multiple entries
                'sources': sources,  # Multiple entries
                'related_docs': related_docs,  # Multiple entries
                'images': site_images,  # Multiple entries
                'evidences': site_evidences_list,
            }
            sites_with_details.append(site_data)

        # Evidences linked directly to research (not linked to a site)
        direct_evidence_ids = ArchEvResearch.objects.filter(
            id_research=research.id
        ).values_list('id_archaeological_evidence_id', flat=True)
        direct_evidences = ArchaeologicalEvidence.objects.filter(id__in=direct_evidence_ids)

        # For each evidence, get its related data
        evidences_with_details = []
        for evidence in direct_evidences:
            # Get ALL bibliographies for this evidence
            ev_biblios = ArchEvBiblio.objects.filter(id_archaeological_evidence=evidence).select_related('id_bibliography')
            bibliographies = [eb.id_bibliography for eb in ev_biblios]

            # Get ALL sources for this evidence
            ev_sources_links = ArchEvSources.objects.filter(id_archaeological_evidence=evidence).select_related('id_sources')
            sources = [es.id_sources for es in ev_sources_links]

            # Get ALL related docs for this evidence
            related_docs = ArchEvRelatedDoc.objects.filter(id_archaeological_evidence=evidence)

            # Get ALL images for this evidence
            ev_images = Image.objects.filter(id_archaeological_evidence=evidence)

            evidence_data = {
                'evidence': evidence,
                'bibliographies': bibliographies,  # Multiple entries
                'sources': sources,  # Multiple entries
                'related_docs': related_docs,  # Multiple entries
                'images': ev_images,  # Multiple entries
            }
            evidences_with_details.append(evidence_data)

        context['sites_with_details'] = sites_with_details
        context['evidences_with_details'] = evidences_with_details
        context['authors'] = authors

        # Create Folium map for research geometry
        map_html = None
        if research.geometry:
            map_html = create_folium_map(
                research.geometry,
                research_title=research.title or "Research Area"
            )
        context['map_html'] = map_html
        context['research_owner'] = research.submitted_by if research.submitted_by else None

        return context


class ResearchUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Research
    form_class = ResearchForm
    template_name = 'frontend/research_form.html'

    def get_success_url(self):
        return reverse_lazy('user-researches', kwargs={'username': self.request.user.username})

    def get_initial(self):
        initial = super().get_initial()
        research = self.get_object()
        # All model fields are automatically prefilled by ModelForm
        # This just ensures geometry and other fields are available
        initial['title'] = research.title
        initial['year'] = research.year
        initial['keywords'] = research.keywords
        initial['abstract'] = research.abstract
        initial['type'] = research.type
        initial['geometry'] = research.geometry
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        research = self.get_object()

        # Get existing authors for this research
        author_ids = ResearchAuthor.objects.filter(id_research=research).values_list('id_author_id', flat=True).distinct()
        authors = User.objects.filter(id__in=author_ids).select_related('profile')
        context['existing_authors'] = authors

        return context

    def form_valid(self, form):
        # Handle shapefile → geometry
        shapefile = self.request.FILES.get('shapefile')
        if shapefile:
            try:
                geometry = extract_geometry_from_shapefile(shapefile)
                form.instance.geometry = geometry
            except ValidationError as e:
                form.add_error('shapefile', e)
                return self.form_invalid(form)

        # Save research
        form.instance.submitted_by = self.request.user
        self.object = form.save()

        # Update authors - remove old and add new
        # First, delete existing author relationships for this research
        ResearchAuthor.objects.filter(id_research=self.object).delete()

        # Handle main author
        is_self_author = self.request.POST.get('is_self_author')
        if is_self_author == 'yes':
            author_user = self.request.user
        else:
            user_id = self.request.POST.get('author_user_id')

            if user_id:
                author_user = get_object_or_404(User, pk=user_id)
                affiliation = self.request.POST.get('author_affiliation', '')
                orcid = self.request.POST.get('author_orcid', '')
                author_user = get_or_update_user_profile(author_user, affiliation=affiliation, orcid=orcid)
            else:
                author_name = self.request.POST.get('author_name')
                author_surname = self.request.POST.get('author_surname')
                author_email = self.request.POST.get('author_email')
                affiliation = self.request.POST.get('author_affiliation', '')
                orcid = self.request.POST.get('author_orcid', '')

                if not author_name or not author_surname or not author_email:
                    form.add_error(None, 'Name, surname, and email are required for new author')
                    return self.form_invalid(form)

                author_user = find_or_create_user_as_author(
                    author_name, author_surname, author_email,
                    affiliation=affiliation, orcid=orcid
                )

        ResearchAuthor.objects.get_or_create(id_research=self.object, id_author=author_user)

        index = 0
        while True:
            co_user_id = self.request.POST.get(f'coauthor_user_id_{index}')

            if co_user_id:
                co_user = User.objects.filter(pk=co_user_id).first()
                if co_user:
                    co_affiliation = self.request.POST.get(f'coauthor_affiliation_{index}', '')
                    co_orcid = self.request.POST.get(f'coauthor_orcid_{index}', '')
                    co_user = get_or_update_user_profile(co_user, affiliation=co_affiliation, orcid=co_orcid)
                    ResearchAuthor.objects.get_or_create(id_research=self.object, id_author=co_user)
            else:
                name = self.request.POST.get(f'coauthor_name_{index}')
                surname = self.request.POST.get(f'coauthor_surname_{index}')
                email = self.request.POST.get(f'coauthor_email_{index}')

                if name and surname and email:
                    co_affiliation = self.request.POST.get(f'coauthor_affiliation_{index}', '')
                    co_orcid = self.request.POST.get(f'coauthor_orcid_{index}', '')
                    co_user = find_or_create_user_as_author(
                        name, surname, email,
                        affiliation=co_affiliation, orcid=co_orcid
                    )
                    ResearchAuthor.objects.get_or_create(id_research=self.object, id_author=co_user)
                else:
                    break
            index += 1

        return HttpResponseRedirect(self.get_success_url())

    def test_func(self):
        """
        Allow admin to update any research, or user to update their own research
        """
        research = self.get_object()
        return self.request.user.is_staff or self.request.user == research.submitted_by


class ResearchDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Research
    template_name = 'frontend/research_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('user-researches', kwargs={'username': self.request.user.username})

    def test_func(self):
        """
        Allow admin to update any research, or user to update their own research
        """
        research = self.get_object()
        return self.request.user.is_staff or self.request.user == research.submitted_by


def load_typologies(request):
    functional_class_id = request.GET.get('functional_class')
    typologies = Typology.objects.filter(id_functional_class=functional_class_id).values('id', 'desc_typology')
    return JsonResponse(list(typologies), safe=False)


def load_typology_details(request):
    typology_id = request.GET.get('typology')
    details = TypologyDetail.objects.filter(id_typology=typology_id).values('id', 'desc_typology_detail')
    return JsonResponse(list(details), safe=False)


def load_provinces(request):
    codice_regione = request.GET.get('region')
    if not codice_regione:
        return JsonResponse([], safe=False)
    try:
        region_id = int(codice_regione)
    except (ValueError, TypeError):
        return JsonResponse([], safe=False)
    provinces = Province.objects.filter(codice_regione=region_id).values(
        'id', 'sigla_provincia', 'denominazione_provincia'
    )
    return JsonResponse(list(provinces), safe=False)


def load_municipalities(request):
    id_province = request.GET.get("province")
    if not id_province:
        return JsonResponse([], safe=False)

    municipalities = Municipality.objects.filter(id_province=id_province).values("id", "denominazione_comune")
    return JsonResponse(list(municipalities), safe=False)


@login_required
@require_POST
def preview_shapefile(request):
    if not request.FILES.get('shapefile'):
        return JsonResponse({'error': 'No shapefile provided'}, status=400)
    try:
        geometry_text = extract_geometry_from_shapefile(request.FILES['shapefile'])
        return JsonResponse({'geometry': geometry_text})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def preview_shapefile_geojson(request):
    """Return all shapefile features as a GeoJSON FeatureCollection (for Evidence)."""
    if not request.FILES.get('shapefile'):
        return JsonResponse({'error': 'No shapefile provided'}, status=400)
    try:
        from .shapefile_utils import extract_geojson_from_shapefile
        geojson = extract_geojson_from_shapefile(request.FILES['shapefile'])
        return JsonResponse({'geojson': geojson})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def search_authors(request):
    """
    Search for users to add as authors to research.
    Searches only in auth_user and users_profile tables (single source of truth).
    No Author table lookups - User is the only source of truth.
    """
    query = request.GET.get('q', '').strip()
    results = []

    if query and len(query) >= 3:

        # Search by last_name (surname) in User model - highest priority
        user_surname_matches = User.objects.filter(
            last_name__icontains=query
        ).select_related('profile').distinct()[:10]

        seen_users = set()

        def add_user_result(user, match_type):
            """Helper to add user result if not already seen"""
            if user.id in seen_users:
                return
            seen_users.add(user.id)

            # Get profile if exists
            try:
                profile = user.profile
            except Exception:
                profile = None

            results.append({
                'type': 'user',
                'user_id': user.id,
                'username': user.username,
                'name': user.first_name or '',
                'surname': user.last_name or '',
                'email': user.email or '',
                'affiliation': profile.affiliation if profile else '',
                'orcid': profile.orcid if profile else '',
                'contact_email': profile.contact_email if profile else '',
                'match_type': match_type
            })

        # Process surname matches (highest priority)
        for user in user_surname_matches:
            add_user_result(user, 'surname')

        # Search by first_name (name) - medium priority
        remaining_slots = 10 - len(results)
        if remaining_slots > 0:
            user_firstname_matches = User.objects.filter(
                first_name__icontains=query
            ).exclude(id__in=seen_users).select_related('profile').distinct()[:remaining_slots]

            for user in user_firstname_matches:
                add_user_result(user, 'firstname')

        # Search by username - medium-low priority
        remaining_slots = 10 - len(results)
        if remaining_slots > 0:
            user_username_matches = User.objects.filter(
                username__icontains=query
            ).exclude(id__in=seen_users).select_related('profile').distinct()[:remaining_slots]

            for user in user_username_matches:
                add_user_result(user, 'username')

        # Search by email - lowest priority
        remaining_slots = 10 - len(results)
        if remaining_slots > 0:
            user_email_matches = User.objects.filter(
                email__icontains=query
            ).exclude(id__in=seen_users).select_related('profile').distinct()[:remaining_slots]

            for user in user_email_matches:
                add_user_result(user, 'email')

    return JsonResponse(results[:10], safe=False)


class SiteCreateView(LoginRequiredMixin, CreateView):
    model = Site
    form_class = SiteForm
    template_name = 'frontend/site_form.html'

    def get_success_url(self):
        research_id = self.request.GET.get('research_id')
        if research_id:
            return reverse('research-detail', args=[research_id])
        return reverse('evidence_list')  # fallback if no research_id

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chronologies'] = Chronology.objects.all()
        context['source_types'] = SourcesType.objects.all()
        context['image_types'] = ImageType.objects.all()
        context['image_scales'] = ImageScale.objects.all()
        return context

    def form_valid(self, form):

        # Optional: build geometry from lat/lon
        lat = form.cleaned_data.get('lat')
        lon = form.cleaned_data.get('lon')
        if lat and lon:
            form.instance.geometry = (float(lon), float(lat))

        response = super().form_valid(form)  # Save the Site instance
        site = self.object

        # Save SiteToponymy
        ancient_name = form.cleaned_data.get('ancient_place_name')
        contemporary_name = form.cleaned_data.get('contemporary_place_name')

        if ancient_name or contemporary_name:
            SiteToponymy.objects.create(
                id_site=site,
                ancient_place_name=ancient_name,
                contemporary_place_name=contemporary_name
            )

        # Save Interpretation
        functional_class = form.cleaned_data.get('functional_class')
        typology = form.cleaned_data.get('typology')
        typology_detail = form.cleaned_data.get('typology_detail')
        chronology = form.cleaned_data.get('chronology')
        certainty = form.cleaned_data.get('chronology_certainty_level') or 1

        if functional_class or typology or typology_detail or chronology:
            Interpretation.objects.create(
                id_site=site,
                id_functional_class=functional_class,
                id_typology=typology,
                id_typology_detail=typology_detail,
                id_chronology=chronology,
                chronology_certainty_level=certainty
            )

        # Save SiteResearch relationship
        research_id = self.request.GET.get('research_id')
        if research_id:
            try:
                research = Research.objects.get(pk=research_id)
                SiteResearch.objects.get_or_create(id_site=site, id_research=research)
            except Research.DoesNotExist:
                pass

        # Save Investigation
        project_name = form.cleaned_data.get('project_name')
        periodo = form.cleaned_data.get('periodo')
        investigation_type = form.cleaned_data.get('investigation_type')

        if project_name and periodo and investigation_type:
            investigation, created = Investigation.objects.update_or_create(
                project_name=project_name,
                defaults={
                    'period': periodo,
                    'id_investigation_type': investigation_type
                }
            )
            # Associate the investigation with the site
            SiteInvestigation.objects.update_or_create(
                id_site=site,
                id_investigation=investigation
            )

        # Save multiple bibliographies
        # Collect all bibliography fields from POST data
        biblio_index = 0
        while True:
            title = self.request.POST.get(f'biblio_title_{biblio_index}')
            author = self.request.POST.get(f'biblio_author_{biblio_index}')
            year = self.request.POST.get(f'biblio_year_{biblio_index}')
            doi = self.request.POST.get(f'biblio_doi_{biblio_index}')
            tipo = self.request.POST.get(f'biblio_tipo_{biblio_index}')

            # Break if no more bibliography entries
            if title is None:
                break

            # Only save if at least one field is filled
            if title or author or year or doi or tipo:
                bibliography = Bibliography.objects.create(
                    title=title or '',
                    author=author or '',
                    year=int(year) if year else None,
                    doi=doi or '',
                    tipo=tipo or ''
                )
                SiteBibliography.objects.create(
                    id_site=site,
                    id_bibliography=bibliography
                )

            biblio_index += 1

        # Save multiple sources
        source_index = 0
        while True:
            source_name = self.request.POST.get(f'source_name_{source_index}')
            if source_name is None:
                break

            # Only save if at least one field is filled
            chronology_id = self.request.POST.get(f'source_chronology_{source_index}')
            source_type_id = self.request.POST.get(f'source_type_{source_index}')

            if source_name or chronology_id or source_type_id:
                source = Sources.objects.create(
                    name=source_name or '',
                    id_chronology_id=chronology_id if chronology_id else None,
                    id_sources_typology_id=source_type_id if source_type_id else None
                )
                SiteSources.objects.create(
                    id_site=site,
                    id_sources=source
                )

            source_index += 1

        # Save multiple related documentations
        doc_index = 0
        while True:
            doc_name = self.request.POST.get(f'doc_name_{doc_index}')
            if doc_name is None:
                break

            # Only save if at least one field is filled
            doc_author = self.request.POST.get(f'doc_author_{doc_index}')
            doc_year = self.request.POST.get(f'doc_year_{doc_index}')

            if doc_name or doc_author or doc_year:
                SiteRelatedDocumentation.objects.create(
                    id_site=site,
                    name=doc_name or '',
                    author=doc_author or '',
                    year=int(doc_year) if doc_year else None
                )

            doc_index += 1

        # Save multiple images
        image_index = 0
        while True:
            image_type_id = self.request.POST.get(f'image_type_{image_index}')
            if image_type_id is None:
                break

            # Collect all image fields
            image_scale_id = self.request.POST.get(f'image_scale_{image_index}')
            file_name = self.request.POST.get(f'image_file_name_{image_index}')
            acquisition_date = self.request.POST.get(f'image_acquisition_date_{image_index}')
            desc_image = self.request.POST.get(f'image_desc_{image_index}')
            format_field = self.request.POST.get(f'image_format_{image_index}')
            projection = self.request.POST.get(f'image_projection_{image_index}')
            spatial_resolution = self.request.POST.get(f'image_spatial_resolution_{image_index}')
            author = self.request.POST.get(f'image_author_{image_index}')
            upload_type_img = self.request.POST.get(f'image_upload_type_{image_index}', 'url')

            # Handle image source URL or file upload
            source_url = None
            if upload_type_img == 'url':
                source_url = self.request.POST.get(f'image_source_url_{image_index}')
            else:
                # File upload - save to media folder
                image_file = self.request.FILES.get(f'image_file_{image_index}')
                if image_file:
                    # Validate file is actually an image
                    if hasattr(image_file, 'content_type') and str(image_file.content_type).startswith('image/'):
                        source_url = save_uploaded_image(image_file, subfolder='site_images')

            key_words = self.request.POST.get(f'image_key_words_{image_index}')

            # Only save if at least one field is filled
            if any([image_type_id, image_scale_id, file_name, acquisition_date, desc_image,
                    format_field, projection, spatial_resolution, author, source_url, key_words]):
                Image.objects.create(
                    id_site=site,
                    file_name=file_name or '',
                    acquisition_date=acquisition_date if acquisition_date else None,
                    desc_image=desc_image or '',
                    id_image_scale=image_scale_id if image_scale_id else None,
                    id_image_type=image_type_id if image_type_id else None,
                    format=format_field or '',
                    projection=projection or '',
                    spatial_resolution=spatial_resolution or '',
                    author=author or '',
                    source_url=source_url or '',
                    key_words=key_words or ''
                )

            image_index += 1

        return response


class SiteListView(LoginRequiredMixin, ListView):
    """
    Display a list of sites, optionally filtered by research_id query parameter.
    Usage: /sites/?research_id=<id>
    """
    model = Site
    template_name = 'frontend/site_list.html'
    context_object_name = 'sites'

    def get_queryset(self):
        queryset = Site.objects.all()
        research_id = self.request.GET.get('research_id')
        if research_id:
            queryset = queryset.filter(siteresearch__id_research=research_id)
        return queryset


class SiteDetailView(DetailView):
    model = Site
    template_name = 'frontend/site_detail.html'
    context_object_name = 'site'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site = self.object

        # Basic site information
        context['site_toponymy'] = SiteToponymy.objects.filter(id_site=site.id).first()
        context['interpretation'] = Interpretation.objects.filter(id_site=site.id).first()
        context['site_investigation'] = SiteInvestigation.objects.filter(id_site=site).select_related('id_investigation').first()

        # Related evidences
        site_evidence_links = SiteArchEvidence.objects.filter(
            id_site=site
        ).select_related('id_archaeological_evidence')
        context['site_evidences'] = [link.id_archaeological_evidence for link in site_evidence_links]

        # Related researches
        site_research_links = SiteResearch.objects.filter(id_site=site).select_related('id_research')
        context['site_researches'] = [link.id_research for link in site_research_links]

        # Multiple bibliographies (all entries)
        site_biblios = SiteBibliography.objects.filter(id_site=site).select_related('id_bibliography')
        context['site_bibliographies'] = [sb.id_bibliography for sb in site_biblios]

        # Multiple sources (all entries)
        site_sources = SiteSources.objects.filter(id_site=site).select_related('id_sources')
        context['site_sources'] = [ss.id_sources for ss in site_sources]

        # Multiple related documentation (all entries)
        context['site_docs'] = SiteRelatedDocumentation.objects.filter(id_site=site)

        # Multiple images (all entries)
        context['site_images'] = Image.objects.filter(id_site=site)

        # Create Folium map for site geometry
        map_html = None
        if site.geometry:
            map_html = create_folium_map(
                site.geometry,
                research_title=site.site_name or "Site Location"
            )
        context['map_html'] = map_html

        return context


class SiteUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Site
    form_class = SiteForm
    template_name = 'frontend/site_form.html'

    def get_success_url(self):
        research_id = self.request.GET.get('research_id')
        if research_id:
            return reverse('research-detail', args=[research_id])
        return reverse('evidence_list')  # fallback if no research_id

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site = self.get_object()

        # Context data for dropdown options
        context['chronologies'] = Chronology.objects.all()
        context['source_types'] = SourcesType.objects.all()
        context['image_types'] = ImageType.objects.all()
        context['image_scales'] = ImageScale.objects.all()

        # Get all bibliographies for this site
        site_biblios = SiteBibliography.objects.filter(id_site=site).select_related('id_bibliography')
        bibliographies = [sb.id_bibliography for sb in site_biblios]
        context['existing_bibliographies'] = bibliographies

        # Get all sources for this site
        site_sources = SiteSources.objects.filter(id_site=site).select_related('id_sources')
        sources = [ss.id_sources for ss in site_sources]
        context['existing_sources'] = sources

        # Get all related documentations for this site
        docs = SiteRelatedDocumentation.objects.filter(id_site=site)
        context['existing_docs'] = docs

        # Get all images for this site
        images = Image.objects.filter(id_site=site)
        context['existing_images'] = images

        return context

    def get_initial(self):
        initial = super().get_initial()
        site = self.get_object()

        # Site model fields
        initial['site_name'] = site.site_name
        initial['site_environment_relationship'] = site.site_environment_relationship
        initial['additional_topography'] = site.additional_topography
        initial['elevation'] = site.elevation
        initial['id_country'] = site.id_country
        initial['id_region'] = site.id_region
        initial['id_province'] = site.id_province
        initial['id_municipality'] = site.id_municipality
        initial['id_physiography'] = site.id_physiography
        initial['id_base_map'] = site.id_base_map
        initial['id_positioning_mode'] = site.id_positioning_mode
        initial['id_positional_accuracy'] = site.id_positional_accuracy
        initial['id_first_discovery_method'] = site.id_first_discovery_method
        initial['locality_name'] = site.locality_name
        initial['lat'] = site.lat
        initial['lon'] = site.lon
        initial['geometry'] = site.geometry
        initial['description'] = site.description
        initial['notes'] = site.notes

        # SiteToponymy
        try:
            toponymy = SiteToponymy.objects.get(id_site=site.id)
            initial['ancient_place_name'] = toponymy.ancient_place_name
            initial['contemporary_place_name'] = toponymy.contemporary_place_name
        except SiteToponymy.DoesNotExist:
            pass

        # Interpretation
        try:
            interp = Interpretation.objects.get(id_site=site.id)
            initial['functional_class'] = interp.id_functional_class
            initial['typology'] = interp.id_typology
            initial['typology_detail'] = interp.id_typology_detail
            initial['chronology'] = interp.id_chronology
            initial['chronology_certainty_level'] = interp.chronology_certainty_level
        except Interpretation.DoesNotExist:
            pass

        # Investigation
        site_investigation = SiteInvestigation.objects.filter(id_site=site.id).first()
        if site_investigation and site_investigation.id_investigation:
            investigation = site_investigation.id_investigation
            initial['project_name'] = investigation.project_name
            initial['periodo'] = investigation.period
            initial['investigation_type'] = investigation.id_investigation_type

        # SiteBibliography - get first if multiple exist
        site_biblio = SiteBibliography.objects.select_related('id_bibliography').filter(id_site=site.id).first()
        if site_biblio:
            biblio = site_biblio.id_bibliography  # Access the related Bibliography
            initial['title'] = biblio.title
            initial['author'] = biblio.author
            initial['year'] = biblio.year
            initial['doi'] = biblio.doi
            initial['tipo'] = biblio.tipo

        # SiteSources - get first if multiple exist
        site_sources = SiteSources.objects.select_related('id_sources').filter(id_site=site.id).first()
        if site_sources:
            source = site_sources.id_sources
            initial['name'] = source.name
            initial['documentation_chronology'] = source.id_chronology
            initial['source_type'] = source.id_sources_typology

        # SiteRelatedDocumentation - get first if multiple exist
        site_doc = SiteRelatedDocumentation.objects.filter(id_site=site.id).first()
        if site_doc:
            initial['documentation_name'] = site_doc.name
            initial['documentation_author'] = site_doc.author
            initial['documentation_year'] = site_doc.year

        # Image - get first if multiple exist
        image = Image.objects.filter(id_site=site.id).first()
        if image:
            initial['image_type'] = image.id_image_type
            initial['image_scale'] = image.id_image_scale

        return initial

    def form_valid(self, form):
        lat = form.cleaned_data.get('lat')
        lon = form.cleaned_data.get('lon')
        if lat and lon:
            form.instance.geometry = (float(lon), float(lat))

        response = super().form_valid(form)
        site = self.object

        # Update SiteToponymy
        SiteToponymy.objects.update_or_create(
            id_site=site,
            defaults={
                'ancient_place_name': form.cleaned_data.get('ancient_place_name'),
                'contemporary_place_name': form.cleaned_data.get('contemporary_place_name')
            }
        )

        # Update Interpretation
        if form.cleaned_data.get('functional_class'):
            Interpretation.objects.update_or_create(
                id_site=site,
                defaults={
                    'id_functional_class': form.cleaned_data.get('functional_class'),
                    'id_typology': form.cleaned_data.get('typology'),
                    'id_typology_detail': form.cleaned_data.get('typology_detail'),
                    'id_chronology': form.cleaned_data.get('chronology'),
                    'chronology_certainty_level': form.cleaned_data.get('chronology_certainty_level') or 1
                }
            )
        # Update SiteResearch relationship
        research_id = self.request.GET.get('research_id')
        if research_id:
            try:
                research = Research.objects.get(pk=research_id)
                SiteResearch.objects.update_or_create(
                    id_site=site,
                    id_research=research
                )
            except Research.DoesNotExist:
                pass

        # Update Investigation
        project_name = form.cleaned_data.get('project_name')
        periodo = form.cleaned_data.get('periodo')
        investigation_type = form.cleaned_data.get('investigation_type')

        # Delete all old investigations for this site first
        SiteInvestigation.objects.filter(id_site=site).delete()

        if project_name and periodo and investigation_type:
            investigation, created = Investigation.objects.update_or_create(
                project_name = project_name,
                defaults={
                    'period': periodo,
                    'id_investigation_type': investigation_type
                }
            )
            # Associate the investigation with the site
            SiteInvestigation.objects.create(
                id_site=site,
                id_investigation=investigation
            )

        # Update site bibliographies - remove all old ones and create new ones
        # First, delete existing bibliographies for this site
        SiteBibliography.objects.filter(id_site=site).delete()

        # Now save all bibliographies from the form
        biblio_index = 0
        while True:
            title = self.request.POST.get(f'biblio_title_{biblio_index}')
            author = self.request.POST.get(f'biblio_author_{biblio_index}')
            year = self.request.POST.get(f'biblio_year_{biblio_index}')
            doi = self.request.POST.get(f'biblio_doi_{biblio_index}')
            tipo = self.request.POST.get(f'biblio_tipo_{biblio_index}')

            # Break if no more bibliography entries
            if title is None:
                break

            # Only save if at least one field is filled
            if title or author or year or doi or tipo:
                bibliography = Bibliography.objects.create(
                    title=title or '',
                    author=author or '',
                    year=int(year) if year else None,
                    doi=doi or '',
                    tipo=tipo or ''
                )
                SiteBibliography.objects.create(
                    id_site=site,
                    id_bibliography=bibliography
                )

            biblio_index += 1

        # Update site sources - remove all old ones and create new ones
        # First, delete existing sources for this site
        SiteSources.objects.filter(id_site=site).delete()

        # Now save all sources from the form
        source_index = 0
        while True:
            source_name = self.request.POST.get(f'source_name_{source_index}')
            if source_name is None:
                break

            # Collect all source fields
            chronology_id = self.request.POST.get(f'source_chronology_{source_index}')
            source_type_id = self.request.POST.get(f'source_type_{source_index}')

            if source_name or chronology_id or source_type_id:
                source = Sources.objects.create(
                    name=source_name or '',
                    id_chronology_id=chronology_id if chronology_id else None,
                    id_sources_typology_id=source_type_id if source_type_id else None
                )
                SiteSources.objects.create(
                    id_site=site,
                    id_sources=source
                )

            source_index += 1

        # Update site related documentation - remove all old ones and create new ones
        # First, delete existing docs for this site
        SiteRelatedDocumentation.objects.filter(id_site=site).delete()

        # Now save all docs from the form
        doc_index = 0
        while True:
            doc_name = self.request.POST.get(f'doc_name_{doc_index}')
            if doc_name is None:
                break

            # Only save if at least one field is filled
            doc_author = self.request.POST.get(f'doc_author_{doc_index}')
            doc_year = self.request.POST.get(f'doc_year_{doc_index}')

            if doc_name or doc_author or doc_year:
                SiteRelatedDocumentation.objects.create(
                    id_site=site,
                    name=doc_name or '',
                    author=doc_author or '',
                    year=int(doc_year) if doc_year else None
                )

            doc_index += 1

        # Update site related images - remove all old ones and create new ones
        # First, delete existing images for this site
        Image.objects.filter(id_site=site).delete()

        # Now save all images from the form
        image_index = 0
        while True:
            image_type_id = self.request.POST.get(f'image_type_{image_index}')
            if image_type_id is None:
                break

            # Collect all image fields
            image_scale_id = self.request.POST.get(f'image_scale_{image_index}')
            file_name = self.request.POST.get(f'image_file_name_{image_index}')
            acquisition_date = self.request.POST.get(f'image_acquisition_date_{image_index}')
            desc_image = self.request.POST.get(f'image_desc_{image_index}')
            format_field = self.request.POST.get(f'image_format_{image_index}')
            projection = self.request.POST.get(f'image_projection_{image_index}')
            spatial_resolution = self.request.POST.get(f'image_spatial_resolution_{image_index}')
            author = self.request.POST.get(f'image_author_{image_index}')
            upload_type_img = self.request.POST.get(f'image_upload_type_{image_index}', 'url')

            # Handle image source URL or file upload
            source_url = None
            if upload_type_img == 'url':
                source_url = self.request.POST.get(f'image_source_url_{image_index}')
            else:
                # File upload - save to media folder
                image_file = self.request.FILES.get(f'image_file_{image_index}')
                if image_file:
                    # Validate file is actually an image
                    if hasattr(image_file, 'content_type') and str(image_file.content_type).startswith('image/'):
                        source_url = save_uploaded_image(image_file, subfolder='site_images')

            key_words = self.request.POST.get(f'image_key_words_{image_index}')

            # Only save if at least one field is filled
            if any([image_type_id, image_scale_id, file_name, acquisition_date, desc_image,
                    format_field, projection, spatial_resolution, author, source_url, key_words]):
                Image.objects.create(
                    id_site=site,
                    file_name=file_name or '',
                    acquisition_date=acquisition_date if acquisition_date else None,
                    desc_image=desc_image or '',
                    id_image_scale=image_scale_id if image_scale_id else None,
                    id_image_type=image_type_id if image_type_id else None,
                    format=format_field or '',
                    projection=projection or '',
                    spatial_resolution=spatial_resolution or '',
                    author=author or '',
                    source_url=source_url or '',
                    key_words=key_words or ''
                )

            image_index += 1

        return response

    def test_func(self):
        """
        Allow admin to update any site, or user to update sites linked to their research.
        If no research is linked, allow admin or authenticated users.
        """
        site = self.get_object()
        # Admins can update any site
        if self.request.user.is_staff:
            return True
        # Check if user owns the research associated with this site
        site_research = SiteResearch.objects.filter(id_site=site).first()
        if site_research and site_research.id_research:
            return self.request.user == site_research.id_research.submitted_by
        # If no research linked, allow authenticated users
        return self.request.user.is_authenticated


class SiteDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Site
    template_name = 'frontend/site_confirm_delete.html'

    def test_func(self):
        """
        Allow admin to delete any site, or user to delete sites linked to their research.
        If no research is linked, allow admin or authenticated users.
        """
        site = self.get_object()
        # Admins can delete any site
        if self.request.user.is_staff:
            return True
        # Check if user owns the research associated with this site
        site_research = SiteResearch.objects.filter(id_site=site).first()
        if site_research and site_research.id_research:
            return self.request.user == site_research.id_research.submitted_by
        # If no research linked, allow authenticated users
        return self.request.user.is_authenticated

    def get_success_url(self):
        # Get the research ID through the SiteResearch relationship
        site = self.object
        site_research = site.siteresearch_set.first()
        if site_research:
            return reverse('research-detail', args=[site_research.id_research.id])
        return reverse('site_list')  # fallback if no research is linked


class EvidenceCreateView(LoginRequiredMixin, CreateView):
    model = ArchaeologicalEvidence
    form_class = ArchaeologicalEvidenceForm
    template_name = 'frontend/evidence_form.html'

    def get_success_url(self):
        research_id = self.request.GET.get('research_id')
        if research_id:
            return reverse('research-detail', args=[research_id])
        return reverse('evidence_list')  # fallback if no research_id

    def form_valid(self, form):
        response = super().form_valid(form)
        arch_ev = self.object

        # Save relation with Research or Site
        research_id = self.request.GET.get('research_id')
        site_id = self.request.GET.get('site_id')

        if research_id:
            try:
                research = Research.objects.get(pk=research_id)
                ArchEvResearch.objects.update_or_create(
                    id_archaeological_evidence=arch_ev,
                    defaults={'id_research': research.id}
                )
            except Research.DoesNotExist:
                pass

        if site_id:
            try:
                site = Site.objects.get(pk=site_id)
                SiteArchEvidence.objects.update_or_create(
                    id_site=site,
                    id_archaeological_evidence=arch_ev
                )
            except Site.DoesNotExist:
                pass

        # Save multiple bibliographies
        # Collect all bibliography fields from POST data
        biblio_index = 0
        while True:
            title = self.request.POST.get(f'ev_biblio_title_{biblio_index}')
            author = self.request.POST.get(f'ev_biblio_author_{biblio_index}')
            year = self.request.POST.get(f'ev_biblio_year_{biblio_index}')
            doi = self.request.POST.get(f'ev_biblio_doi_{biblio_index}')
            tipo = self.request.POST.get(f'ev_biblio_tipo_{biblio_index}')

            # Break if no more bibliography entries
            if title is None:
                break

            # Only save if at least one field is filled
            if title or author or year or doi or tipo:
                bibliography = Bibliography.objects.create(
                    title=title or '',
                    author=author or '',
                    year=int(year) if year else None,
                    doi=doi or '',
                    tipo=tipo or ''
                )
                ArchEvBiblio.objects.create(
                    id_archaeological_evidence=arch_ev,
                    id_bibliography=bibliography
                )

            biblio_index += 1

        # Save sources - using multi-entry pattern from form
        ev_source_index = 0
        while True:
            source_name = self.request.POST.get(f'ev_source_name_{ev_source_index}')
            if source_name is None:
                break
            id_chronology = self.request.POST.get(f'ev_source_chronology_{ev_source_index}')
            id_source_type = self.request.POST.get(f'ev_source_type_{ev_source_index}')
            if source_name or id_chronology or id_source_type:
                source = Sources.objects.create(
                    name=source_name or '',
                    id_chronology_id=id_chronology if id_chronology else None,
                    id_sources_typology_id=id_source_type if id_source_type else None
                )
                ArchEvSources.objects.create(
                    id_archaeological_evidence=arch_ev,
                    id_sources=source
                )
            ev_source_index += 1

        # Save multiple Related Docs - using multi-entry pattern
        ev_doc_index = 0
        while True:
            doc_name = self.request.POST.get(f'ev_doc_name_{ev_doc_index}')
            if doc_name is None:
                break
            doc_author = self.request.POST.get(f'ev_doc_author_{ev_doc_index}')
            doc_year = self.request.POST.get(f'ev_doc_year_{ev_doc_index}')
            if doc_name or doc_author or doc_year:
                ArchEvRelatedDoc.objects.create(
                    id_archaeological_evidence=arch_ev,
                    name=doc_name or '',
                    author=doc_author or '',
                    year=int(doc_year) if doc_year else None
                )
            ev_doc_index += 1

        # Save multiple Images - using multi-entry pattern
        from .models import Image
        ev_image_index = 0
        while True:
            file_name = self.request.POST.get(f'ev_image_file_name_{ev_image_index}')
            if file_name is None:
                break

            # Get all image fields
            image_type_id = self.request.POST.get(f'ev_image_type_{ev_image_index}')
            image_scale_id = self.request.POST.get(f'ev_image_scale_{ev_image_index}')
            acquisition_date = self.request.POST.get(f'ev_image_acquisition_date_{ev_image_index}')
            desc_image = self.request.POST.get(f'ev_image_desc_{ev_image_index}')
            format_val = self.request.POST.get(f'ev_image_format_{ev_image_index}')
            projection = self.request.POST.get(f'ev_image_projection_{ev_image_index}')
            spatial_resolution = self.request.POST.get(f'ev_image_spatial_resolution_{ev_image_index}')
            author = self.request.POST.get(f'ev_image_author_{ev_image_index}')
            key_words = self.request.POST.get(f'ev_image_key_words_{ev_image_index}')
            upload_type = self.request.POST.get(f'ev_image_upload_type_{ev_image_index}', 'url')

            # Handle URL or file upload
            source_url = None
            if upload_type == 'url':
                source_url = self.request.POST.get(f'ev_image_source_url_{ev_image_index}')
            else:
                # Handle file upload - save to media folder
                file_key = f'ev_image_file_{ev_image_index}'
                if file_key in self.request.FILES:
                    uploaded_file = self.request.FILES[file_key]
                    # Validate file type and save
                    if hasattr(uploaded_file, 'content_type') and str(uploaded_file.content_type).startswith('image/'):
                        source_url = save_uploaded_image(uploaded_file, subfolder='evidence_images')

            # Only save if at least one significant field is filled
            if file_name or image_type_id or desc_image or source_url:
                Image.objects.create(
                    id_archaeological_evidence=arch_ev,
                    file_name=file_name or '',
                    id_image_type=image_type_id if image_type_id else None,
                    id_image_scale=image_scale_id if image_scale_id else None,
                    acquisition_date=acquisition_date if acquisition_date else None,
                    desc_image=desc_image or '',
                    format=format_val or '',
                    projection=projection or '',
                    spatial_resolution=spatial_resolution or '',
                    author=author or '',
                    source_url=source_url or '',
                    key_words=key_words or ''
                )

            ev_image_index += 1

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Options for dropdowns
        context['chronologies'] = Chronology.objects.all()
        context['source_types'] = SourcesType.objects.all()
        context['image_types'] = ImageType.objects.all()
        context['image_scales'] = ImageScale.objects.all()
        return context


class EvidenceListView(LoginRequiredMixin, ListView):
    model = ArchaeologicalEvidence
    template_name = 'frontend/evidence_list.html'
    context_object_name = 'evidences'

    def get_queryset(self):
        queryset = ArchaeologicalEvidence.objects.all()
        research_id = self.request.GET.get('research_id')
        if research_id:
            queryset = queryset.filter(archaeologicalevidenceresearch__id_research=research_id)
        return queryset

class EvidenceDetailView(DetailView):
    model = ArchaeologicalEvidence
    template_name = 'frontend/evidence_detail.html'
    context_object_name = 'evidence'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        evidence = self.object

        # Multiple bibliographies (all entries)
        ev_biblios = ArchEvBiblio.objects.filter(id_archaeological_evidence=evidence.id).select_related('id_bibliography')
        context['arch_ev_bibliographies'] = [eb.id_bibliography for eb in ev_biblios]

        # Multiple sources (all entries)
        ev_sources = ArchEvSources.objects.filter(id_archaeological_evidence=evidence.id).select_related('id_sources')
        context['arch_ev_sources'] = [es.id_sources for es in ev_sources]

        # Multiple related documentation (all entries)
        context['arch_ev_related_docs'] = ArchEvRelatedDoc.objects.filter(id_archaeological_evidence=evidence.id)

        # Multiple images (all entries)
        context['evidence_images'] = Image.objects.filter(id_archaeological_evidence=evidence)

        # Related sites
        site_links = SiteArchEvidence.objects.filter(
            id_archaeological_evidence=evidence
        ).select_related('id_site')
        context['sites'] = [link.id_site for link in site_links]

        # Related researches (direct and via sites)
        direct_research_ids = ArchEvResearch.objects.filter(
            id_archaeological_evidence=evidence
        ).values_list('id_research', flat=True)
        research_ids = set(direct_research_ids)
        if site_links:
            site_ids = [link.id_site_id for link in site_links]
            via_sites = SiteResearch.objects.filter(id_site_id__in=site_ids).values_list('id_research_id', flat=True)
            research_ids.update(via_sites)
        context['researches'] = Research.objects.filter(id__in=research_ids) if research_ids else []

        # Investigation information
        if evidence.id_investigation:
            context['investigation'] = evidence.id_investigation

        # Pass geometry as GeoJSON for Leaflet rendering.
        # Supports both the new GeoJSON format and the legacy ((lon,lat),...) format.
        geometry_geojson = None
        if evidence.geometry:
            raw = evidence.geometry.strip()
            if raw.startswith('{') or raw.startswith('['):
                # Already GeoJSON
                geometry_geojson = raw
            else:
                # Legacy format: convert to GeoJSON Polygon
                from .utils.geometry import parse_geometry_string
                coords = parse_geometry_string(raw)
                if coords:
                    geometry_geojson = json.dumps({
                        "type": "FeatureCollection",
                        "features": [{
                            "type": "Feature",
                            "geometry": {"type": "Polygon", "coordinates": [[[lon, lat] for lat, lon in coords]]},
                            "properties": {}
                        }]
                    })
        context['geometry_geojson'] = geometry_geojson

        return context

class EvidenceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ArchaeologicalEvidence
    form_class = ArchaeologicalEvidenceForm
    template_name = 'frontend/evidence_form.html'

    def get_success_url(self):
        research_id = self.request.GET.get('research_id')
        if research_id:
            return reverse('research-detail', args=[research_id])
        return reverse('evidence_list')  # fallback if no research_id

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        evidence = self.get_object()
        # Get all bibliographies for this evidence
        arch_ev_biblios = ArchEvBiblio.objects.filter(id_archaeological_evidence=evidence).select_related('id_bibliography')
        bibliographies = [ab.id_bibliography for ab in arch_ev_biblios]
        context['existing_bibliographies'] = bibliographies
        # Get existing sources
        ev_sources = ArchEvSources.objects.filter(id_archaeological_evidence=evidence).select_related('id_sources')
        context['existing_sources'] = [ev.id_sources for ev in ev_sources]
        # Get existing docs
        ev_docs = ArchEvRelatedDoc.objects.filter(id_archaeological_evidence=evidence)
        context['existing_docs'] = list(ev_docs)
        # Get existing images
        from .models import Image
        existing_images = Image.objects.filter(id_archaeological_evidence=evidence)
        context['existing_images'] = list(existing_images)
        # Options for dropdowns
        context['chronologies'] = Chronology.objects.all()
        context['source_types'] = SourcesType.objects.all()
        context['image_types'] = ImageType.objects.all()
        context['image_scales'] = ImageScale.objects.all()
        return context

    def get_initial(self):
        initial = super().get_initial()
        evidence = self.get_object()

        # Model fields
        initial['evidence_name'] = evidence.evidence_name
        initial['description'] = evidence.description
        initial['id_country'] = evidence.id_country
        initial['id_region'] = evidence.id_region
        initial['id_province'] = evidence.id_province
        initial['id_municipality'] = evidence.id_municipality
        initial['id_archaeological_evidence_typology'] = evidence.id_archaeological_evidence_typology
        initial['id_chronology'] = evidence.id_chronology
        initial['id_positioning_mode'] = evidence.id_positioning_mode
        initial['id_positional_accuracy'] = evidence.id_positional_accuracy
        initial['id_physiography'] = evidence.id_physiography
        initial['id_first_discovery_method'] = evidence.id_first_discovery_method
        initial['notes'] = evidence.notes

        # Investigation fields
        if evidence.id_investigation:
            initial['project_name'] = evidence.id_investigation.project_name
            initial['periodo'] = evidence.id_investigation.period
            initial['investigation_type'] = evidence.id_investigation.id_investigation_type

        # Related bibliography
        biblio = getattr(evidence.archevbiblio_set.first(), 'id_bibliography', None)
        if biblio:
            initial['title'] = biblio.title
            initial['author'] = biblio.author
            initial['year'] = biblio.year
            initial['doi'] = biblio.doi
            initial['type'] = biblio.tipo

        # Sources
        source = getattr(evidence.archevsources_set.first(), 'id_sources', None)
        if source:
            initial['name'] = source.name
            initial['documentation_chronology'] = source.id_chronology
            initial['source_type'] = source.id_sources_typology

        # Related doc
        related_doc = evidence.archevrelateddoc_set.first()
        if related_doc:
            initial['documentation_name'] = related_doc.name
            initial['documentation_author'] = related_doc.author
            initial['documentation_year'] = related_doc.year

        return initial

    def form_valid(self, form):
        # Handle empty geometry field - convert to None to avoid "invalid input syntax for type polygon" error
        geometry = form.cleaned_data.get('geometry')
        if not geometry or geometry.strip() == '':
            form.instance.geometry = None

        response = super().form_valid(form)
        arch_ev = self.object

        # Save/update Investigation
        project_name = form.cleaned_data.get('project_name')
        periodo = form.cleaned_data.get('periodo')
        investigation_type = form.cleaned_data.get('investigation_type')
        if project_name and periodo and investigation_type:
            investigation, _ = Investigation.objects.update_or_create(
                project_name=project_name,
                defaults={
                    'period': periodo,
                    'id_investigation_type': investigation_type
                }
            )
            arch_ev.id_investigation = investigation
            arch_ev.save()

        # Save/update Multiple Bibliographies - remove all old ones and create new ones
        # First, delete existing bibliographies for this evidence
        ArchEvBiblio.objects.filter(id_archaeological_evidence=arch_ev).delete()

        # Now save all bibliographies from the form
        biblio_index = 0
        while True:
            title = self.request.POST.get(f'ev_biblio_title_{biblio_index}')
            author = self.request.POST.get(f'ev_biblio_author_{biblio_index}')
            year = self.request.POST.get(f'ev_biblio_year_{biblio_index}')
            doi = self.request.POST.get(f'ev_biblio_doi_{biblio_index}')
            tipo = self.request.POST.get(f'ev_biblio_tipo_{biblio_index}')

            # Break if no more bibliography entries
            if title is None:
                break

            # Only save if at least one field is filled
            if title or author or year or doi or tipo:
                bibliography = Bibliography.objects.create(
                    title=title or '',
                    author=author or '',
                    year=int(year) if year else None,
                    doi=doi or '',
                    tipo=tipo or ''
                )
                ArchEvBiblio.objects.create(
                    id_archaeological_evidence=arch_ev,
                    id_bibliography=bibliography
                )

            biblio_index += 1

        # Save/update Multiple Sources - remove all old and create new ones
        ArchEvSources.objects.filter(id_archaeological_evidence=arch_ev).delete()
        ev_source_index = 0
        while True:
            source_name = self.request.POST.get(f'ev_source_name_{ev_source_index}')
            if source_name is None:
                break
            id_chronology = self.request.POST.get(f'ev_source_chronology_{ev_source_index}')
            id_source_type = self.request.POST.get(f'ev_source_type_{ev_source_index}')
            if source_name or id_chronology or id_source_type:
                source = Sources.objects.create(
                    name=source_name or '',
                    id_chronology_id=id_chronology if id_chronology else None,
                    id_sources_typology_id=id_source_type if id_source_type else None
                )
                ArchEvSources.objects.create(
                    id_archaeological_evidence=arch_ev,
                    id_sources=source
                )
            ev_source_index += 1

        # Save/update Multiple Related Docs - remove all old and create new ones
        ArchEvRelatedDoc.objects.filter(id_archaeological_evidence=arch_ev).delete()
        ev_doc_index = 0
        while True:
            doc_name = self.request.POST.get(f'ev_doc_name_{ev_doc_index}')
            if doc_name is None:
                break
            doc_author = self.request.POST.get(f'ev_doc_author_{ev_doc_index}')
            doc_year = self.request.POST.get(f'ev_doc_year_{ev_doc_index}')
            if doc_name or doc_author or doc_year:
                ArchEvRelatedDoc.objects.create(
                    id_archaeological_evidence=arch_ev,
                    name=doc_name or '',
                    author=doc_author or '',
                    year=int(doc_year) if doc_year else None
                )
            ev_doc_index += 1

        # Save/update Multiple Images - remove all old and create new ones
        from .models import Image
        Image.objects.filter(id_archaeological_evidence=arch_ev).delete()
        ev_image_index = 0
        while True:
            file_name = self.request.POST.get(f'ev_image_file_name_{ev_image_index}')
            if file_name is None:
                break

            # Get all image fields
            image_type_id = self.request.POST.get(f'ev_image_type_{ev_image_index}')
            image_scale_id = self.request.POST.get(f'ev_image_scale_{ev_image_index}')
            acquisition_date = self.request.POST.get(f'ev_image_acquisition_date_{ev_image_index}')
            desc_image = self.request.POST.get(f'ev_image_desc_{ev_image_index}')
            format_val = self.request.POST.get(f'ev_image_format_{ev_image_index}')
            projection = self.request.POST.get(f'ev_image_projection_{ev_image_index}')
            spatial_resolution = self.request.POST.get(f'ev_image_spatial_resolution_{ev_image_index}')
            author = self.request.POST.get(f'ev_image_author_{ev_image_index}')
            key_words = self.request.POST.get(f'ev_image_key_words_{ev_image_index}')
            upload_type = self.request.POST.get(f'ev_image_upload_type_{ev_image_index}', 'url')

            # Handle URL or file upload
            source_url = None
            if upload_type == 'url':
                source_url = self.request.POST.get(f'ev_image_source_url_{ev_image_index}')
            else:
                # Handle file upload - save to media folder
                file_key = f'ev_image_file_{ev_image_index}'
                if file_key in self.request.FILES:
                    uploaded_file = self.request.FILES[file_key]
                    # Validate file type and save
                    if hasattr(uploaded_file, 'content_type') and str(uploaded_file.content_type).startswith('image/'):
                        source_url = save_uploaded_image(uploaded_file, subfolder='evidence_images')

            # Only save if at least one significant field is filled
            if file_name or image_type_id or desc_image or source_url:
                Image.objects.create(
                    id_archaeological_evidence=arch_ev,
                    file_name=file_name or '',
                    id_image_type=image_type_id if image_type_id else None,
                    id_image_scale=image_scale_id if image_scale_id else None,
                    acquisition_date=acquisition_date if acquisition_date else None,
                    desc_image=desc_image or '',
                    format=format_val or '',
                    projection=projection or '',
                    spatial_resolution=spatial_resolution or '',
                    author=author or '',
                    source_url=source_url or '',
                    key_words=key_words or ''
                )

            ev_image_index += 1

        return response

    def test_func(self):
        """
        Allow admin to update any evidence, or user to update evidence linked to their research.
        If no research is linked, allow admin or authenticated users.
        """
        evidence = self.get_object()
        # Admins can update any evidence
        if self.request.user.is_staff:
            return True
        # Check if user owns the research associated with this evidence
        arch_ev_research = ArchEvResearch.objects.filter(id_archaeological_evidence=evidence).first()
        if arch_ev_research and arch_ev_research.id_research:
            try:
                research = Research.objects.get(pk=arch_ev_research.id_research)
                return self.request.user == research.submitted_by
            except Research.DoesNotExist:
                pass
        # If no research linked, allow authenticated users
        return self.request.user.is_authenticated

class EvidenceDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = ArchaeologicalEvidence
    template_name = 'frontend/evidence_confirm_delete.html'

    def get_success_url(self):
        """
        Try to redirect to the research detail page if evidence is linked to a research.
        Otherwise, redirect to evidence list.
        """
        evidence = self.object
        arch_ev_research = ArchEvResearch.objects.filter(id_archaeological_evidence=evidence).first()
        if arch_ev_research and arch_ev_research.id_research:
            try:
                research = Research.objects.get(pk=arch_ev_research.id_research)
                return reverse('research-detail', args=[research.id])
            except Research.DoesNotExist:
                pass
        return reverse('evidence_list')

    def test_func(self):
        """
        Allow admin to delete any evidence, or user to delete evidence linked to their research.
        If no research is linked, allow admin or authenticated users.
        """
        evidence = self.get_object()
        # Admins can delete any evidence
        if self.request.user.is_staff:
            return True
        # Check if user owns the research associated with this evidence
        arch_ev_research = ArchEvResearch.objects.filter(id_archaeological_evidence=evidence).first()
        if arch_ev_research and arch_ev_research.id_research:
            try:
                research = Research.objects.get(pk=arch_ev_research.id_research)
                return self.request.user == research.submitted_by
            except Research.DoesNotExist:
                pass
        # If no research linked, allow authenticated users
        return self.request.user.is_authenticated


def is_staff(user):
    return user.is_authenticated and user.is_staff



@login_required
def search_users_autocomplete(request):
    """
    AJAX endpoint for autocomplete user search in research author selection.
    Searches by surname, username, or email.
    """
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'results': []})

    # Search users by surname, username, or email
    users = User.objects.filter(
        models.Q(last_name__icontains=query) |
        models.Q(username__icontains=query) |
        models.Q(email__icontains=query)
    ).select_related('profile')[:10]

    results = []
    for user in users:
        # Get user profile info if available
        affiliation = ''
        orcid = ''

        if hasattr(user, 'profile'):
            affiliation = getattr(user.profile, 'affiliation', '') or ''
            orcid = getattr(user.profile, 'orcid', '') or ''

        # User is the single source of truth for author data (no Author table)

        results.append({
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': f"{user.first_name} {user.last_name}",
            'affiliation': affiliation,
            'orcid': orcid,
        })

    return JsonResponse({'results': results})


@login_required
@user_passes_test(is_staff)
def database_browser(request):
    """
    Staff-only view to browse all database tables and their content
    Shows related data for foreign keys instead of just IDs
    """
    # Get all table names from the database
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cursor.fetchall()]

    # Get the selected table (from query parameter)
    selected_table = request.GET.get('table', None)
    page_number = request.GET.get('page', 1)

    table_data = None
    columns = None
    paginator = None
    page_obj = None
    col_names = None
    total_rows = 0
    foreign_keys_info = {}
    display_columns = {}

    if selected_table and selected_table in tables:
        from psycopg2 import sql

        # Get column names and data types
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = %s
                ORDER BY ordinal_position;
            """, [selected_table])
            columns = cursor.fetchall()

        # Get foreign key relationships
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    kcu.column_name AS fk_column,
                    ccu.table_name AS referenced_table,
                    ccu.column_name AS referenced_column
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_name = %s
                    AND tc.table_schema = 'public';
            """, [selected_table])
            fk_relations = cursor.fetchall()

            # Build foreign keys info dictionary
            for fk_col, ref_table, ref_col in fk_relations:
                foreign_keys_info[fk_col] = {
                    'referenced_table': ref_table,
                    'referenced_column': ref_col
                }

        # For each foreign key, determine which column to display from the referenced table
        # Try common patterns: name, title, description, etc.
        display_columns = {}
        for fk_col, fk_info in foreign_keys_info.items():
            ref_table = fk_info['referenced_table']
            with connection.cursor() as cursor:
                # Try to find a display column (name, title, description, etc.)
                cursor.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = %s
                    AND column_name IN ('name', 'title', 'description', 'denominazione_regione',
                                        'denominazione_provincia', 'denominazione_comune',
                                        'site_name', 'desc_positioning_mode', 'desc_physiography',
                                        'desc_base_map', 'desc_first_discovery_method', 'desc_investigation_type',
                                        'chronological_period', 'name_country', 'username', 'surname')
                    ORDER BY CASE column_name
                        WHEN 'name' THEN 1
                        WHEN 'title' THEN 2
                        WHEN 'site_name' THEN 3
                        WHEN 'denominazione_regione' THEN 4
                        WHEN 'denominazione_provincia' THEN 5
                        WHEN 'denominazione_comune' THEN 6
                        ELSE 10
                    END
                    LIMIT 1;
                """, [ref_table])
                result = cursor.fetchone()
                if result:
                    display_columns[fk_col] = result[0]
                else:
                    # Fallback: use the first text/varchar column
                    cursor.execute("""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                        AND table_name = %s
                        AND data_type IN ('text', 'character varying', 'varchar', 'char')
                        ORDER BY ordinal_position
                        LIMIT 1;
                    """, [ref_table])
                    result = cursor.fetchone()
                    if result:
                        display_columns[fk_col] = result[0]
                    else:
                        # Last resort: use the referenced column itself
                        display_columns[fk_col] = fk_info['referenced_column']

        # Get row count
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(selected_table))
            )
            total_rows = cursor.fetchone()[0]

        # Build query with LEFT JOINs for foreign keys
        offset = (int(page_number) - 1) * 100

        # Start building the SELECT clause
        select_parts = [sql.SQL("{}.*").format(sql.Identifier(selected_table))]
        join_parts = []

        # Add JOINs for each foreign key
        for fk_col, fk_info in foreign_keys_info.items():
            ref_table = fk_info['referenced_table']
            ref_col = fk_info['referenced_column']
            display_col = display_columns.get(fk_col, ref_col)
            alias = f"fk_{fk_col}"
            display_alias = f"{fk_col}_display"

            # Add display column to SELECT
            select_parts.append(
                sql.SQL("{}.{} AS {}").format(
                    sql.Identifier(alias),
                    sql.Identifier(display_col),
                    sql.Identifier(display_alias)
                )
            )

            # Add JOIN
            join_parts.append(
                sql.SQL("LEFT JOIN {} AS {} ON {}.{} = {}.{}").format(
                    sql.Identifier(ref_table),
                    sql.Identifier(alias),
                    sql.Identifier(selected_table),
                    sql.Identifier(fk_col),
                    sql.Identifier(alias),
                    sql.Identifier(ref_col)
                )
            )
        # Build final query
        query = sql.SQL("SELECT {} FROM {} {} LIMIT 100 OFFSET %s").format(
            sql.SQL(", ").join(select_parts),
            sql.Identifier(selected_table),
            sql.SQL(" ").join(join_parts) if join_parts else sql.SQL("")
        )

        # Execute query
        with connection.cursor() as cursor:
            cursor.execute(query, [offset])
            table_data = cursor.fetchall()

            # Get column names for display
            col_names = [desc[0] for desc in cursor.description]

        # Process table data to combine foreign key IDs with their display values
        processed_data = []
        for row in table_data:
            processed_row = []
            row_dict = dict(zip(col_names, row))

            for col_name in col_names:
                if col_name.endswith('_display'):
                    # Skip display columns, they'll be shown with their IDs
                    continue

                value = row_dict.get(col_name)
                display_value = row_dict.get(f"{col_name}_display")

                if col_name in foreign_keys_info:
                    # This is a foreign key column
                    processed_row.append({
                        'value': value,
                        'display': display_value,  # Can be None if FK is NULL or join failed
                        'is_fk': True,
                        'fk_table': foreign_keys_info[col_name]['referenced_table']
                    })
                else:
                    # Regular column
                    processed_row.append({
                        'value': value,
                        'display': None,
                        'is_fk': False
                    })

            processed_data.append(processed_row)

        # Filter column names to exclude _display columns
        display_col_names = [col for col in col_names if not col.endswith('_display')]

        # Create paginator
        paginator = Paginator(range(total_rows), 100)
        page_obj = paginator.get_page(page_number)
    else:
        processed_data = None
        display_col_names = None

    pk_col = _get_pk_column(selected_table) if selected_table and selected_table in tables else None

    context = {
        'tables': tables,
        'selected_table': selected_table,
        'table_data': processed_data,
        'columns': columns,
        'col_names': display_col_names,
        'page_obj': page_obj,
        'total_rows': total_rows,
        'foreign_keys_info': foreign_keys_info,
        'display_columns': display_columns,
        'pk_col': pk_col,
    }

    return render(request, 'frontend/database_browser.html', context)


# ── DB Browser CRUD helpers ────────────────────────────────────────────────

def _get_tables():
    with connection.cursor() as cur:
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        return [r[0] for r in cur.fetchall()]

def _get_pk_column(table):
    """Return the first primary-key column name for *table*, or None."""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
              AND tc.table_schema = 'public'
              AND tc.table_name = %s
            ORDER BY kcu.ordinal_position
            LIMIT 1
        """, [table])
        row = cur.fetchone()
        return row[0] if row else None

def _get_columns(table):
    """Return list of (column_name, data_type, is_nullable) for *table*."""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
        """, [table])
        return cur.fetchall()

def _get_fk_info(table):
    """Return dict {col: {referenced_table, referenced_column}} for *table*."""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT kcu.column_name, ccu.table_name, ccu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = 'public'
              AND tc.table_name = %s
        """, [table])
        return {r[0]: {'referenced_table': r[1], 'referenced_column': r[2]}
                for r in cur.fetchall()}


@login_required
@user_passes_test(is_staff)
def db_row_get(request):
    """Return a single row as JSON for the edit modal."""
    from psycopg2 import sql as pgsql
    table = request.GET.get('table', '')
    pk_col = request.GET.get('pk_col', '')
    pk_val = request.GET.get('pk_val', '')

    if not table or table not in _get_tables():
        return JsonResponse({'error': 'Invalid table'}, status=400)

    cols = _get_columns(table)
    col_names = [c[0] for c in cols]
    if pk_col not in col_names:
        return JsonResponse({'error': 'Invalid pk column'}, status=400)

    fk_info = _get_fk_info(table)

    # Fetch the row
    with connection.cursor() as cur:
        cur.execute(
            pgsql.SQL("SELECT * FROM {} WHERE {} = %s LIMIT 1").format(
                pgsql.Identifier(table), pgsql.Identifier(pk_col)
            ), [pk_val]
        )
        row = cur.fetchone()
    if not row:
        return JsonResponse({'error': 'Row not found'}, status=404)

    row_dict = dict(zip(col_names, row))

    # For FK columns, fetch dropdown options (id + display label, max 500)
    fk_options = {}
    for col, info in fk_info.items():
        ref_table = info['referenced_table']
        ref_col = info['referenced_column']
        # Pick a display column
        with connection.cursor() as cur:
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_schema='public' AND table_name=%s
                  AND column_name IN ('name','title','site_name','username','surname','denominazione_regione')
                ORDER BY CASE column_name
                    WHEN 'name' THEN 1 WHEN 'title' THEN 2 WHEN 'site_name' THEN 3
                    WHEN 'username' THEN 4 ELSE 5 END LIMIT 1
            """, [ref_table])
            disp = cur.fetchone()
            display_col = disp[0] if disp else ref_col
            cur.execute(
                pgsql.SQL("SELECT {}, {} FROM {} ORDER BY {} LIMIT 500").format(
                    pgsql.Identifier(ref_col), pgsql.Identifier(display_col),
                    pgsql.Identifier(ref_table), pgsql.Identifier(ref_col)
                )
            )
            fk_options[col] = [
                {'id': str(r[0]), 'label': str(r[1]) if r[1] else str(r[0])}
                for r in cur.fetchall()
            ]

    # Serialise row values to strings (handles dates, decimals, etc.)
    serialised = {k: (str(v) if v is not None else '') for k, v in row_dict.items()}

    return JsonResponse({
        'row': serialised,
        'columns': [{'name': c[0], 'type': c[1], 'nullable': c[2]} for c in cols],
        'fk_info': {k: v for k, v in fk_info.items()},
        'fk_options': fk_options,
    })


@login_required
@user_passes_test(is_staff)
def db_check_dependencies(request):
    """Return tables/counts that reference a given row (pre-delete check)."""
    from psycopg2 import sql as pgsql
    table = request.GET.get('table', '')
    pk_col = request.GET.get('pk_col', '')
    pk_val = request.GET.get('pk_val', '')

    tables = _get_tables()
    if not table or table not in tables:
        return JsonResponse({'error': 'Invalid table'}, status=400)

    # Find all FKs in any table that point to this table
    with connection.cursor() as cur:
        cur.execute("""
            SELECT kcu.table_name, kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = 'public'
              AND ccu.table_name = %s
              AND ccu.column_name = %s
        """, [table, pk_col])
        refs = cur.fetchall()

    deps = []
    for ref_table, ref_col in refs:
        if ref_table not in tables:
            continue
        with connection.cursor() as cur:
            cur.execute(
                pgsql.SQL("SELECT COUNT(*) FROM {} WHERE {} = %s").format(
                    pgsql.Identifier(ref_table), pgsql.Identifier(ref_col)
                ), [pk_val]
            )
            count = cur.fetchone()[0]
        if count > 0:
            deps.append({'table': ref_table, 'column': ref_col, 'count': count})

    return JsonResponse({'dependencies': deps})


@login_required
@user_passes_test(is_staff)
@require_POST
def db_row_save(request):
    """Create or update a row. POST body is JSON."""
    import json
    from psycopg2 import sql as pgsql

    try:
        body = json.loads(request.body)
    except ValueError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    table = body.get('table', '')
    pk_col = body.get('pk_col', '')
    pk_val = body.get('pk_val')          # None → insert, value → update
    fields = body.get('fields', {})      # {col: value}

    tables = _get_tables()
    if not table or table not in tables:
        return JsonResponse({'error': 'Invalid table'}, status=400)

    cols = _get_columns(table)
    valid_cols = {c[0] for c in cols}
    # Sanitise: only accept known column names
    fields = {k: (v if v != '' else None) for k, v in fields.items() if k in valid_cols and k != pk_col}
    if not fields:
        return JsonResponse({'error': 'No fields to save'}, status=400)

    try:
        with connection.cursor() as cur:
            if pk_val:
                # UPDATE
                if pk_col not in valid_cols:
                    return JsonResponse({'error': 'Invalid pk column'}, status=400)
                set_clause = pgsql.SQL(', ').join(
                    pgsql.SQL("{} = %s").format(pgsql.Identifier(k)) for k in fields
                )
                cur.execute(
                    pgsql.SQL("UPDATE {} SET {} WHERE {} = %s").format(
                        pgsql.Identifier(table),
                        set_clause,
                        pgsql.Identifier(pk_col),
                    ),
                    list(fields.values()) + [pk_val]
                )
                action = 'updated'
            else:
                # INSERT
                col_sql = pgsql.SQL(', ').join(pgsql.Identifier(k) for k in fields)
                val_sql = pgsql.SQL(', ').join(pgsql.SQL('%s') for _ in fields)
                cur.execute(
                    pgsql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                        pgsql.Identifier(table), col_sql, val_sql
                    ),
                    list(fields.values())
                )
                action = 'created'
        logger.info("DB Browser %s: table=%s pk=%s by user=%s", action, table, pk_val, request.user)
        return JsonResponse({'success': True, 'action': action})
    except Exception as exc:
        logger.exception("DB Browser save error table=%s", table)
        return JsonResponse({'error': str(exc)}, status=500)


@login_required
@user_passes_test(is_staff)
@require_POST
def db_row_delete(request):
    """Delete a row. POST body is JSON. Requires force=true if deps exist."""
    import json
    from psycopg2 import sql as pgsql

    try:
        body = json.loads(request.body)
    except ValueError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    table = body.get('table', '')
    pk_col = body.get('pk_col', '')
    pk_val = body.get('pk_val')
    force = body.get('force', False)

    tables = _get_tables()
    if not table or table not in tables:
        return JsonResponse({'error': 'Invalid table'}, status=400)

    cols = _get_columns(table)
    if pk_col not in {c[0] for c in cols}:
        return JsonResponse({'error': 'Invalid pk column'}, status=400)

    # Dependency check unless caller confirmed with force=true
    if not force:
        with connection.cursor() as cur:
            cur.execute("""
                SELECT kcu.table_name, kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_schema = 'public'
                  AND ccu.table_name = %s AND ccu.column_name = %s
            """, [table, pk_col])
            refs = cur.fetchall()
        deps = []
        for ref_table, ref_col in refs:
            if ref_table not in tables:
                continue
            with connection.cursor() as cur:
                cur.execute(
                    pgsql.SQL("SELECT COUNT(*) FROM {} WHERE {} = %s").format(
                        pgsql.Identifier(ref_table), pgsql.Identifier(ref_col)
                    ), [pk_val]
                )
                count = cur.fetchone()[0]
            if count > 0:
                deps.append({'table': ref_table, 'column': ref_col, 'count': count})
        if deps:
            return JsonResponse({'needs_confirm': True, 'dependencies': deps})

    try:
        with connection.cursor() as cur:
            cur.execute(
                pgsql.SQL("DELETE FROM {} WHERE {} = %s").format(
                    pgsql.Identifier(table), pgsql.Identifier(pk_col)
                ), [pk_val]
            )
        logger.info("DB Browser DELETE: table=%s pk_col=%s pk_val=%s by user=%s",
                    table, pk_col, pk_val, request.user)
        return JsonResponse({'success': True})
    except Exception as exc:
        logger.exception("DB Browser delete error table=%s", table)
        return JsonResponse({'error': str(exc)}, status=500)


# ==================== AUDIT LOGGING VIEWS ====================

class AdminOnlyMixin(UserPassesTestMixin):
    """Mixin to restrict access to admin users only"""
    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to access this page. Admin access required.")
        return redirect('home')


class AuditLogListView(LoginRequiredMixin, AdminOnlyMixin, ListView):
    """
    Display audit logs for admin users.
    Shows all operations performed by users in the system.
    """
    paginate_by = 50
    template_name = 'frontend/audit_log_list.html'
    context_object_name = 'logs'

    def get_queryset(self):
        queryset = AuditLog.objects.all().select_related('user')

        operation = self.request.GET.get('operation')
        if operation and operation in ['CREATE', 'UPDATE', 'DELETE', 'VIEW']:
            queryset = queryset.filter(operation=operation)

        model_name = self.request.GET.get('model')
        if model_name:
            queryset = queryset.filter(model_name__icontains=model_name)

        username = self.request.GET.get('user')
        if username:
            queryset = queryset.filter(user__username__icontains=username)

        days = self.request.GET.get('days', '30')
        if days.isdigit():
            since = timezone.now() - timedelta(days=int(days))
            queryset = queryset.filter(timestamp__gte=since)

        return queryset.order_by('-timestamp')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add statistics
        all_logs = AuditLog.objects.all()
        context['total_logs'] = all_logs.count()
        context['create_count'] = all_logs.filter(operation='CREATE').count()
        context['update_count'] = all_logs.filter(operation='UPDATE').count()
        context['delete_count'] = all_logs.filter(operation='DELETE').count()

        # Add filter values
        context['selected_operation'] = self.request.GET.get('operation', '')
        context['selected_model'] = self.request.GET.get('model', '')
        context['selected_user'] = self.request.GET.get('user', '')
        context['selected_days'] = self.request.GET.get('days', '30')

        # Add available models
        context['models'] = sorted(set(all_logs.values_list('model_name', flat=True)))
        context['users'] = User.objects.filter(is_active=True).order_by('username')

        return context


@login_required
def audit_log_export(request):
    """Export audit logs as CSV for admin users"""
    if not request.user.is_staff:
        messages.error(request, "You do not have permission to export logs.")
        return redirect('home')

    queryset = AuditLog.objects.all().select_related('user')

    operation = request.GET.get('operation')
    if operation and operation in ['CREATE', 'UPDATE', 'DELETE', 'VIEW']:
        queryset = queryset.filter(operation=operation)

    model_name = request.GET.get('model')
    if model_name:
        queryset = queryset.filter(model_name__icontains=model_name)

    username = request.GET.get('user')
    if username:
        queryset = queryset.filter(user__username__icontains=username)

    days = request.GET.get('days', '30')
    if days.isdigit():
        since = timezone.now() - timedelta(days=int(days))
        queryset = queryset.filter(timestamp__gte=since)

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'

    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'User', 'Operation', 'Model', 'Object ID', 'Object', 'Changes', 'IP Address'])

    for log in queryset.order_by('-timestamp'):
        writer.writerow([
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.user.username if log.user else 'Anonymous',
            log.operation,
            log.model_name,
            log.object_id,
            log.object_str,
            log.get_changes_display,
            log.ip_address or 'N/A',
        ])

    return response


def is_staff(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_staff)
def export_database(request):
    """
    Export the entire PostgreSQL database as a gzip-compressed plain SQL file.

    Plain SQL format (not -Fc custom format) is used so the backup can be
    restored on any PostgreSQL version — the custom binary format embeds the
    pg_dump version and cannot be read by an older pg_restore (e.g. a dump
    from PG16 fails on a VPS running PG14).

    Uses subprocess.run (blocking) so the full dump is buffered before sending —
    this guarantees we can inspect returncode/stderr before writing any bytes to
    the HTTP response.
    """
    import datetime
    import gzip as _gzip
    db_name = os.environ.get('DB_NAME', getattr(settings, 'DATABASES', {}).get('default', {}).get('NAME'))
    db_user = os.environ.get('DB_USER', getattr(settings, 'DATABASES', {}).get('default', {}).get('USER'))
    db_password = os.environ.get('DB_PASSWORD', getattr(settings, 'DATABASES', {}).get('default', {}).get('PASSWORD'))
    db_host = os.environ.get('DB_HOST', getattr(settings, 'DATABASES', {}).get('default', {}).get('HOST', 'localhost'))
    db_port = os.environ.get('DB_PORT', getattr(settings, 'DATABASES', {}).get('default', {}).get('PORT', '5432'))

    now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{db_name}_backup_{now}.sql.gz"

    env = os.environ.copy()
    env['PGPASSWORD'] = db_password
    cmd = [
        'pg_dump',
        '-U', db_user,
        '-h', db_host,
        '-p', str(db_port),
        # Plain SQL text format: version-agnostic, works across all PG versions.
        # -Fc (custom binary) embeds the pg_dump version and cannot be restored
        # by an older pg_restore on a different server.
        '--no-owner',        # omit ALTER … OWNER TO — restoring user becomes owner
        '--no-privileges',   # omit GRANT/REVOKE — avoids role-not-found errors
        db_name,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, env=env)
        if result.returncode != 0:
            error_msg = result.stderr.decode(errors='replace')
            logger.error("pg_dump failed (db=%s): %s", db_name, error_msg)
            return HttpResponse(
                f"Database export failed:\n{error_msg}",
                status=500,
                content_type='text/plain'
            )
        if result.stderr:
            logger.warning("pg_dump warnings (db=%s): %s", db_name, result.stderr.decode(errors='replace'))
        compressed = _gzip.compress(result.stdout)
        response = HttpResponse(compressed, content_type='application/gzip')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        logger.exception("Unexpected error during pg_dump")
        return HttpResponse(f"Error running pg_dump: {str(e)}", status=500, content_type='text/plain')


@login_required
@user_passes_test(is_staff)
@require_POST
def import_database(request):
    """
    Import a PostgreSQL backup file (.dump or .sql) and restore the database.
    Only staff/admin users can access. Shows double warning in UI.

    Safety measures implemented:
    - Automatic pre-restore backup taken before DROP DATABASE (safety net).
    - Database identifiers quoted with psycopg2.sql.Identifier (no SQL injection).
    - All temp files cleaned in a single finally block (no leak on any path).
    - subprocess.run (blocking) used throughout for predictable error handling.
    """
    import datetime
    import gzip
    import shutil
    import tempfile
    import psycopg2
    from psycopg2 import sql as pgsql
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

    backup_file = request.FILES.get('backup_file')
    if not backup_file:
        return HttpResponse("No file uploaded.", status=400)

    # Track all temp paths so the finally block can clean them unconditionally
    tmp_path = None
    decompressed_path = None
    pre_restore_backup_path = None
    sql_path = None

    try:
        # ── Save uploaded file to disk ─────────────────────────────────────
        with tempfile.NamedTemporaryFile(delete=False, suffix='.upload') as tmp:
            for chunk in backup_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        # ── Decompress if gzip ─────────────────────────────────────────────
        is_gzip = backup_file.name.endswith('.gz')
        if is_gzip:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.decompressed') as tmp_dec:
                decompressed_path = tmp_dec.name
            with gzip.open(tmp_path, 'rb') as gz_in, open(decompressed_path, 'wb') as dec_out:
                dec_out.write(gz_in.read())

        # ── DB credentials ─────────────────────────────────────────────────
        db_name = os.environ.get('DB_NAME', settings.DATABASES.get('default', {}).get('NAME'))
        db_user = os.environ.get('DB_USER', settings.DATABASES.get('default', {}).get('USER'))
        db_password = os.environ.get('DB_PASSWORD', settings.DATABASES.get('default', {}).get('PASSWORD'))
        db_host = os.environ.get('DB_HOST', settings.DATABASES.get('default', {}).get('HOST', 'localhost'))
        db_port = os.environ.get('DB_PORT', settings.DATABASES.get('default', {}).get('PORT', '5432'))

        env = os.environ.copy()
        env['PGPASSWORD'] = db_password
        env['PATH'] = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'

        pg_dump_cmd    = shutil.which('pg_dump',    path=env['PATH']) or '/usr/bin/pg_dump'
        psql_cmd       = shutil.which('psql',       path=env['PATH']) or '/usr/bin/psql'
        pg_restore_cmd = shutil.which('pg_restore', path=env['PATH']) or '/usr/bin/pg_restore'

        # ── Step 1: Automatic pre-restore backup (safety net) ──────────────
        # If the restore fails for any reason the old data is recoverable from
        # this file.  It is deleted only after a successful restore.
        now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        pre_restore_backup_path = f"/tmp/pre_restore_{db_name}_{now}.dump"
        backup_result = subprocess.run(
            [pg_dump_cmd, '-Fc',
             '-U', db_user, '-h', db_host, '-p', str(db_port),
             '-f', pre_restore_backup_path,
             db_name],
            env=env, capture_output=True
        )
        if backup_result.returncode != 0:
            raise Exception(
                "Pre-restore safety backup failed — aborting to protect existing data.\n"
                + backup_result.stderr.decode(errors='replace')
            )
        logger.info("Pre-restore backup saved: %s", pre_restore_backup_path)

        # ── Step 2: Terminate connections, drop, recreate DB ───────────────
        # psycopg2.sql.Identifier safely quotes identifiers — no f-string injection.
        conn = psycopg2.connect(
            dbname='postgres',
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Parameterized value for datname (string literal — use %s, not Identifier)
        cursor.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = %s AND pid <> pg_backend_pid();",
            (db_name,)
        )

        # Identifiers (database / role names) must use sql.Identifier, not %s
        cursor.execute(pgsql.SQL("DROP DATABASE IF EXISTS {}").format(pgsql.Identifier(db_name)))
        cursor.execute(
            pgsql.SQL("CREATE DATABASE {} OWNER {}").format(
                pgsql.Identifier(db_name),
                pgsql.Identifier(db_user),
            )
        )
        cursor.close()
        conn.close()

        # ── Step 3: Restore ────────────────────────────────────────────────
        # --single-transaction wraps all DDL/DML in one BEGIN/COMMIT so the
        # restore is atomic: either every table is created or none are.
        # This prevents the "partial restore" state where pg_restore continues
        # past errors and leaves Django with a database missing some tables.
        restore_target = decompressed_path or tmp_path

        def _rollback_to_pre_restore():
            """Restore the safety backup so Django is left in a working state."""
            if not (pre_restore_backup_path and os.path.exists(pre_restore_backup_path)):
                return False
            logger.warning("Attempting auto-rollback from pre-restore backup: %s", pre_restore_backup_path)
            rb = subprocess.run(
                [pg_restore_cmd, '-O', '--no-privileges', '--single-transaction',
                 '-U', db_user, '-h', db_host, '-p', str(db_port),
                 '-d', db_name, pre_restore_backup_path],
                env=env, capture_output=True, text=True
            )
            if rb.returncode == 0:
                logger.info("Auto-rollback succeeded — database restored to pre-restore state.")
                return True
            logger.error("Auto-rollback failed: %s", rb.stderr)
            return False

        if backup_file.name.endswith('.sql') or (is_gzip and backup_file.name.endswith('.sql.gz')):
            restore_cmd = [
                psql_cmd, '-U', db_user, '-h', db_host, '-p', str(db_port),
                '--single-transaction',
                '-d', db_name, '-f', restore_target,
            ]
        else:
            restore_cmd = [
                pg_restore_cmd, '-O', '--no-privileges', '--single-transaction',
                '-U', db_user, '-h', db_host, '-p', str(db_port),
                '-d', db_name, restore_target,
            ]

        restore = subprocess.run(restore_cmd, env=env, capture_output=True, text=True)

        if restore.returncode != 0:
            if 'unsupported version' in restore.stderr:
                _rollback_to_pre_restore()
                raise Exception(
                    "The backup file format is not compatible with this PostgreSQL version.\n\n"
                    f"Error: {restore.stderr}\n\n"
                    "Please re-export the backup from the source database using:\n"
                    "  pg_dump -U username -h host database_name > backup.sql\n\n"
                    "Then upload the .sql file instead."
                )
            if 'transaction_timeout' in restore.stderr:
                # Convert to plain SQL, strip the offending SET line, re-apply via psql
                with tempfile.NamedTemporaryFile(delete=False, suffix='.sql') as tmp_sql:
                    sql_path = tmp_sql.name
                conv = subprocess.run(
                    [pg_restore_cmd, '-O', '--no-privileges',
                     '-U', db_user, '-h', db_host, '-p', str(db_port),
                     '-f', sql_path, restore_target],
                    env=env, capture_output=True, text=True
                )
                if conv.returncode != 0:
                    _rollback_to_pre_restore()
                    raise Exception(restore.stderr + "\n" + conv.stderr)
                with open(sql_path, 'r') as f:
                    lines = f.readlines()
                with open(sql_path, 'w') as f:
                    for line in lines:
                        if 'transaction_timeout' not in line:
                            f.write(line)
                restore2 = subprocess.run(
                    [psql_cmd, '-U', db_user, '-h', db_host, '-p', str(db_port),
                     '--single-transaction',
                     '-d', db_name, '-f', sql_path],
                    env=env, capture_output=True, text=True
                )
                if restore2.returncode != 0:
                    _rollback_to_pre_restore()
                    raise Exception(restore.stderr + "\n" + restore2.stderr)
            else:
                _rollback_to_pre_restore()
                raise Exception(restore.stderr)

        if restore.stderr:
            logger.warning("pg_restore non-fatal warnings (%s): %s", backup_file.name, restore.stderr)

        # Restore succeeded — pre-restore backup is no longer needed
        if pre_restore_backup_path and os.path.exists(pre_restore_backup_path):
            os.unlink(pre_restore_backup_path)
            pre_restore_backup_path = None

        return render(request, 'frontend/database_import_result.html', {
            'status': 'success',
            'file_name': backup_file.name,
        })

    except Exception as e:
        logger.exception("Database restore failed for file %s", backup_file.name if backup_file else '?')
        return render(request, 'frontend/database_import_result.html', {
            'status': 'error',
            'error_message': str(e),
            'file_name': backup_file.name if backup_file else '',
            # Tell the operator where the pre-restore backup is (if it was created)
            'pre_restore_backup': pre_restore_backup_path,
        }, status=500)

    finally:
        # Always clean up upload/decompress/sql temp files.
        # pre_restore_backup_path is intentionally left on disk on error (recovery use).
        for path in (tmp_path, decompressed_path, sql_path):
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except Exception:
                    pass


# API endpoints for modal selectors
def api_sites_list(request):
    """API endpoint to get list of all sites"""
    try:
        # Fetch ALL sites from database using model instances
        sites_query = Site.objects.all().order_by('site_name')

        print(f"[API] Total sites in database: {sites_query.count()}")

        sites_list = []
        for site in sites_query:
            site_display = {
                'id': site.id,
                'site_name': site.site_name if site.site_name else f"Site #{site.id}",
                'locality_name': site.locality_name if hasattr(site, 'locality_name') else ''
            }
            sites_list.append(site_display)
            print(f"[API] Added site: {site_display}")

        print(f"[API] Total sites to return: {len(sites_list)}")

        return JsonResponse({
            'success': True,
            'count': len(sites_list),
            'results': sites_list
        })
    except Exception as e:
        import traceback
        print(f"[API ERROR] {str(e)}")
        traceback.print_exc()
        return JsonResponse({
            'error': str(e),
            'success': False
        }, status=500)


def api_evidence_list(request):
    """API endpoint to get list of all archaeological evidence"""
    try:
        # Fetch ALL archaeological evidence from database using model instances
        evidence_query = ArchaeologicalEvidence.objects.all().order_by('evidence_name')

        print(f"[API] Total evidence in database: {evidence_query.count()}")

        evidence_list = []
        for evidence in evidence_query:
            evidence_display = {
                'id': evidence.id,
                'evidence_name': evidence.evidence_name if evidence.evidence_name else f"Evidence #{evidence.id}",
                'description': evidence.description if hasattr(evidence, 'description') else ''
            }
            evidence_list.append(evidence_display)
            print(f"[API] Added evidence: {evidence_display}")

        print(f"[API] Total evidence to return: {len(evidence_list)}")

        return JsonResponse({
            'success': True,
            'count': len(evidence_list),
            'results': evidence_list
        })
    except Exception as e:
        import traceback
        print(f"[API ERROR] {str(e)}")
        traceback.print_exc()
        return JsonResponse({
            'error': str(e),
            'success': False
        }, status=500)


def api_site_research_create(request):
    """API endpoint to create a SiteResearch relation"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if not request.user.is_authenticated or (not request.user.is_staff and not request.user.is_superuser):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    try:
        import json
        data = json.loads(request.body)

        site_id = data.get('id_site')
        research_id = data.get('id_research')

        if not site_id or not research_id:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        # Check if relation already exists
        if SiteResearch.objects.filter(id_site=site_id, id_research=research_id).exists():
            return JsonResponse({'error': 'This site is already linked to this research'}, status=400)

        # Create the relation
        site_research = SiteResearch(id_site_id=site_id, id_research_id=research_id)
        site_research.full_clean()
        site_research.save()

        return JsonResponse({'success': True, 'id': site_research.id})
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Site.DoesNotExist:
        return JsonResponse({'error': 'Site not found'}, status=404)
    except Research.DoesNotExist:
        return JsonResponse({'error': 'Research not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def api_site_evidence_create(request):
    """API endpoint to create a SiteArchEvidence relation"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if not request.user.is_authenticated or (not request.user.is_staff and not request.user.is_superuser):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    try:
        import json
        data = json.loads(request.body)

        site_id = data.get('id_site')
        evidence_id = data.get('id_archaeological_evidence')

        if not site_id or not evidence_id:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        # Check if relation already exists
        if SiteArchEvidence.objects.filter(id_site=site_id, id_archaeological_evidence=evidence_id).exists():
            return JsonResponse({'error': 'This evidence is already linked to this site'}, status=400)

        # Create the relation
        site_evidence = SiteArchEvidence(id_site_id=site_id, id_archaeological_evidence_id=evidence_id)
        site_evidence.full_clean()
        site_evidence.save()

        return JsonResponse({'success': True, 'id': site_evidence.id})
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Site.DoesNotExist:
        return JsonResponse({'error': 'Site not found'}, status=404)
    except ArchaeologicalEvidence.DoesNotExist:
        return JsonResponse({'error': 'Evidence not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def api_research_evidence_create(request):
    """API endpoint to create an ArchEvResearch relation"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if not request.user.is_authenticated or (not request.user.is_staff and not request.user.is_superuser):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    try:
        import json
        data = json.loads(request.body)

        print(f"[API DEBUG] Received data: {data}")

        research_id = data.get('id_research')
        evidence_id = data.get('id_archaeological_evidence')

        print(f"[API DEBUG] research_id: {research_id}, evidence_id: {evidence_id}")

        if not research_id or not evidence_id:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        # Verify the research exists
        try:
            Research.objects.get(id=research_id)
        except Research.DoesNotExist:
            return JsonResponse({'error': 'Research not found'}, status=404)

        # Verify the evidence exists
        try:
            evidence = ArchaeologicalEvidence.objects.get(id=evidence_id)
        except ArchaeologicalEvidence.DoesNotExist:
            return JsonResponse({'error': 'Evidence not found'}, status=404)

        # Check if relation already exists
        if ArchEvResearch.objects.filter(id_research=research_id, id_archaeological_evidence=evidence_id).exists():
            return JsonResponse({'error': 'This evidence is already linked to this research'}, status=400)

        # Create the relation - id_research is IntegerField, id_archaeological_evidence is ForeignKey
        research_evidence = ArchEvResearch(
            id_research=research_id,
            id_archaeological_evidence=evidence
        )
        research_evidence.save()

        print(f"[API DEBUG] Successfully created relation: {research_evidence.id}")

        return JsonResponse({'success': True, 'id': research_evidence.id})
    except ValidationError as e:
        print(f"[API ERROR] ValidationError: {e}")
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        import traceback
        print(f"[API ERROR] Unexpected error: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

# ─────────────────────────────────────────────────────────────────
# Admin: User Management
# ─────────────────────────────────────────────────────────────────

class AdminUserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'frontend/admin_user_list.html'
    context_object_name = 'users'
    paginate_by = 25

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        qs = (
            User.objects
            .select_related('profile')
            .prefetch_related('profile__user_roles')
            .order_by('-date_joined')
        )
        q = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '')
        role = self.request.GET.get('role', '')
        if q:
            qs = qs.filter(
                Q(username__icontains=q) |
                Q(email__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q)
            )
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        if role:
            qs = qs.filter(profile__user_roles__role=role).distinct()
        return qs

    def get_context_data(self, **kwargs):
        from users.models import UserRole
        context = super().get_context_data(**kwargs)
        context['total_users'] = User.objects.count()
        context['active_users'] = User.objects.filter(is_active=True).count()
        context['inactive_users'] = User.objects.filter(is_active=False).count()
        context['staff_users'] = User.objects.filter(is_staff=True).count()
        context['all_roles'] = UserRole.objects.filter(is_active=True)
        context['q'] = self.request.GET.get('q', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['role_filter'] = self.request.GET.get('role', '')
        return context


@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_user_create(request):
    from users.models import Profile, UserRole
    all_roles = UserRole.objects.filter(is_active=True)
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password = request.POST.get('password', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        is_staff = request.POST.get('is_staff') == 'on'
        affiliation = request.POST.get('affiliation', '').strip()
        orcid = request.POST.get('orcid', '').strip() or None
        qualification = request.POST.get('qualification', '').strip()
        role_ids = request.POST.getlist('roles')

        errors = []
        if not username:
            errors.append('Username is required.')
        elif User.objects.filter(username=username).exists():
            errors.append('This username is already taken.')
        if email and User.objects.filter(email=email).exists():
            errors.append('This email is already registered.')
        if not password:
            errors.append('Password is required.')
        elif len(password) < 8:
            errors.append('Password must be at least 8 characters.')

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            user = User.objects.create_user(
                username=username, email=email,
                first_name=first_name, last_name=last_name,
                password=password,
                is_active=is_active,
                is_staff=is_staff if request.user.is_superuser else False,
            )
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.affiliation = affiliation or None
            profile.orcid = orcid
            profile.qualification = qualification or None
            if role_ids:
                profile.user_roles.set(UserRole.objects.filter(pk__in=role_ids))
            profile.save()
            messages.success(request, f'User "{username}" created successfully.')
            return redirect('admin_user_list')

    return render(request, 'frontend/admin_user_edit.html', {
        'all_roles': all_roles,
        'form_action': 'create',
        'page_title': 'Create New User',
    })


@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_user_edit(request, pk):
    from users.models import Profile, UserRole
    target_user = get_object_or_404(User, pk=pk)
    profile, _ = Profile.objects.get_or_create(user=target_user)
    all_roles = UserRole.objects.filter(is_active=True)

    if request.method == 'POST':
        if target_user.is_superuser and not request.user.is_superuser:
            messages.error(request, 'Only superusers can edit other superusers.')
            return redirect('admin_user_list')

        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        new_password = request.POST.get('password', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        is_staff = request.POST.get('is_staff') == 'on'
        affiliation = request.POST.get('affiliation', '').strip()
        orcid = request.POST.get('orcid', '').strip() or None
        qualification = request.POST.get('qualification', '').strip()
        role_ids = request.POST.getlist('roles')

        errors = []
        if not username:
            errors.append('Username is required.')
        elif User.objects.filter(username=username).exclude(pk=pk).exists():
            errors.append('This username is already taken.')
        if email and User.objects.filter(email=email).exclude(pk=pk).exists():
            errors.append('This email is already registered to another account.')
        if new_password and len(new_password) < 8:
            errors.append('Password must be at least 8 characters.')

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            target_user.username = username
            target_user.email = email
            target_user.first_name = first_name
            target_user.last_name = last_name
            target_user.is_active = is_active
            if request.user.is_superuser:
                target_user.is_staff = is_staff
            if new_password:
                target_user.set_password(new_password)
            target_user.save()

            profile.affiliation = affiliation or None
            profile.orcid = orcid
            profile.qualification = qualification or None
            profile.user_roles.set(UserRole.objects.filter(pk__in=role_ids))
            profile.save()
            messages.success(request, f'User "{username}" updated successfully.')
            return redirect('admin_user_list')

    return render(request, 'frontend/admin_user_edit.html', {
        'target_user': target_user,
        'profile': profile,
        'all_roles': all_roles,
        'user_role_ids': list(profile.user_roles.values_list('pk', flat=True)),
        'form_action': 'edit',
        'page_title': f'Edit User: {target_user.username}',
    })


@login_required
@user_passes_test(lambda u: u.is_staff)
@require_POST
def admin_user_toggle_active(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    if target_user == request.user:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('admin_user_list')
    if target_user.is_superuser and not request.user.is_superuser:
        messages.error(request, 'Only superusers can deactivate other superusers.')
        return redirect('admin_user_list')
    target_user.is_active = not target_user.is_active
    target_user.save(update_fields=['is_active'])
    status = 'activated' if target_user.is_active else 'deactivated'
    messages.success(request, f'User "{target_user.username}" {status}.')
    return redirect('admin_user_list')


@login_required
@user_passes_test(lambda u: u.is_staff)
@require_POST
def admin_user_delete(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    if target_user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('admin_user_list')
    if target_user.is_superuser and not request.user.is_superuser:
        messages.error(request, 'Only superusers can delete other superusers.')
        return redirect('admin_user_list')
    username = target_user.username
    target_user.delete()
    messages.success(request, f'User "{username}" deleted.')
    return redirect('admin_user_list')


@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_site_settings(request):
    settings_obj = SiteSettings.load()
    if request.method == 'POST':
        # Text / colour fields
        settings_obj.site_name       = request.POST.get('site_name', '').strip() or 'SHAReLAND'
        settings_obj.tagline         = request.POST.get('tagline', '').strip()
        settings_obj.navbar_primary  = request.POST.get('navbar_primary', '#2c3e50')
        settings_obj.navbar_secondary= request.POST.get('navbar_secondary', '#34495e')
        settings_obj.navbar_accent   = request.POST.get('navbar_accent', '#3498db')
        settings_obj.navbar_text     = request.POST.get('navbar_text', '#ecf0f1')
        settings_obj.page_bg         = request.POST.get('page_bg', '#f5f6fa')
        settings_obj.card_accent     = request.POST.get('card_accent', '#3498db')
        settings_obj.footer_text     = request.POST.get('footer_text', '').strip()

        # Logo upload
        if 'logo' in request.FILES:
            settings_obj.logo = request.FILES['logo']
        elif request.POST.get('logo_clear') == 'on':
            settings_obj.logo = None

        # Favicon upload
        if 'favicon' in request.FILES:
            settings_obj.favicon = request.FILES['favicon']
        elif request.POST.get('favicon_clear') == 'on':
            settings_obj.favicon = None

        # ── Home page: About ────────────────────────────────────
        settings_obj.show_about  = request.POST.get('show_about') == 'on'
        settings_obj.about_en    = request.POST.get('about_en', '').strip()
        settings_obj.about_it    = request.POST.get('about_it', '').strip()

        # ── Home page: Key Information ──────────────────────────
        settings_obj.show_keyinfo       = request.POST.get('show_keyinfo') == 'on'
        settings_obj.project_date       = request.POST.get('project_date', '').strip()
        settings_obj.institution_name   = request.POST.get('institution_name', '').strip()
        settings_obj.institution_dept   = request.POST.get('institution_dept', '').strip()
        settings_obj.lab_name           = request.POST.get('lab_name', '').strip()
        settings_obj.lab_instagram      = request.POST.get('lab_instagram', '').strip()
        settings_obj.phd_title          = request.POST.get('phd_title', '').strip()
        settings_obj.phd_researcher     = request.POST.get('phd_researcher', '').strip()
        settings_obj.phd_years          = request.POST.get('phd_years', '').strip()

        # ── Home page: Team ─────────────────────────────────────
        settings_obj.show_team          = request.POST.get('show_team') == 'on'
        settings_obj.team_coordinators  = request.POST.get('team_coordinators', '').strip()
        settings_obj.team_technical     = request.POST.get('team_technical', '').strip()

        # ── Home page: Logos ────────────────────────────────────
        settings_obj.show_logos         = request.POST.get('show_logos') == 'on'
        settings_obj.logo_partner_1_name = request.POST.get('logo_partner_1_name', '').strip()
        settings_obj.logo_partner_2_name = request.POST.get('logo_partner_2_name', '').strip()
        settings_obj.logo_partner_3_name = request.POST.get('logo_partner_3_name', '').strip()
        for slot in ('logo_partner_1', 'logo_partner_2', 'logo_partner_3'):
            if slot in request.FILES:
                setattr(settings_obj, slot, request.FILES[slot])
            elif request.POST.get(f'{slot}_clear') == 'on':
                setattr(settings_obj, slot, None)

        # ── Paesaggi Condivisi poster ───────────────────────────
        if 'poster_lucretili' in request.FILES:
            settings_obj.poster_lucretili = request.FILES['poster_lucretili']
        elif request.POST.get('poster_lucretili_clear') == 'on':
            settings_obj.poster_lucretili = None

        settings_obj.save()
        messages.success(request, 'Site settings saved successfully.')
        return redirect('admin_site_settings')

    return render(request, 'frontend/admin_site_settings.html', {'settings': settings_obj})


@login_required
def platform_manual(request):
    """User manual – authenticated users only."""
    return render(request, 'frontend/platform_manual.html')


def paesaggi_condivisi(request):
    """Paesaggi Archeologici Condivisi – dedicated page."""
    site_cfg = SiteSettings.load()
    return render(request, 'frontend/paesaggi_condivisi.html', {
        'poster': site_cfg.poster_lucretili if site_cfg else None,
    })


def api_debug_data(request):
    """Debug endpoint to check data availability"""
    try:
        sites_count = Site.objects.count()
        evidence_count = ArchaeologicalEvidence.objects.count()

        first_5_sites = list(Site.objects.all()[:5].values('id', 'site_name', 'locality_name'))
        first_5_evidence = list(ArchaeologicalEvidence.objects.all()[:5].values('id', 'evidence_name', 'description'))

        return JsonResponse({
            'database_status': 'connected',
            'sites': {
                'total_count': sites_count,
                'first_5': first_5_sites
            },
            'evidence': {
                'total_count': evidence_count,
                'first_5': first_5_evidence
            }
        })
    except Exception as e:
        import traceback
        print(f"[DEBUG ERROR] {str(e)}")
        traceback.print_exc()
        return JsonResponse({
            'error': str(e),
            'status': 'error'
        }, status=500)
