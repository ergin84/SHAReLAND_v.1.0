# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
import uuid
from django.db import models
from django.contrib.auth.models import User


class Anagraphic(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField(blank=True, null=True)
    surname = models.TextField(blank=True, null=True)
    username = models.TextField(blank=True, null=True)
    password = models.TextField(blank=True, null=True)
    contact_email = models.TextField(blank=True, null=True)


    class Meta:
        db_table = 'anagraphic'
        db_table_comment = 'Ogni utente registrato (anagraphic) può essere anche un autore, ma non è obbligatorio.\t\t\nOgni autore (author) può essere un utente registrato, ma può anche essere una persona esterna al sistema.\t\t\nIl rapporto tra le due tabelle è quindi uno a uno opzionale (1:1 opzionale)\t\t\n'

    def __str__(self):
        return f'{self.name} {self.surname}'


class ArchEvBiblio(models.Model):
    id_archaeological_evidence = models.ForeignKey('ArchaeologicalEvidence', models.DO_NOTHING,
                                                   db_column='id_archaeological_evidence', blank=True, null=True)
    id_bibliography = models.ForeignKey('Bibliography', models.DO_NOTHING, db_column='id_bibliography', blank=True,
                                        null=True)
    id = models.AutoField(primary_key=True)

    class Meta:
        db_table = 'arch_ev_biblio'

    def __str__(self):
        return f'{self.id_archaeological_evidence} - {self.id_bibliography}'


class PositioningMode(models.Model):
    desc_positioning_mode = models.TextField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)

    class Meta:
        db_table = 'positioning_mode'

    def __str__(self):
        return self.desc_positioning_mode


class Country(models.Model):
    name_country = models.CharField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)

    class Meta:
        db_table = 'country'

    def __str__(self):
        return self.name_country


class Region(models.Model):
    ripartizione_geografica = models.TextField(blank=True, null=True)
    codice_regione = models.TextField(blank=True, null=True)
    denominazione_regione = models.TextField(blank=True, null=True)
    tipologia_regione = models.TextField(blank=True, null=True)
    superficie_kmq = models.TextField(blank=True, null=True)
    id_region = models.IntegerField(primary_key=True)

    class Meta:
        db_table = 'region'

    def __str__(self):
        return self.denominazione_regione


class Province(models.Model):
    id = models.IntegerField(primary_key=True)
    codice_regione = models.ForeignKey(Region, to_field='id_region', db_column='codice_regione',
                                       on_delete=models.CASCADE)
    sigla_provincia = models.TextField(blank=True, null=True)
    denominazione_provincia = models.TextField(blank=True, null=True)
    superficie_kmq = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    codice_sovracomunale = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'province'

    def __str__(self):
        return self.denominazione_provincia


class Municipality(models.Model):
    denominazione_comune = models.TextField(blank=True, null=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    lon = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    sigla_provincia = models.CharField(blank=True, null=True)
    id_province = models.ForeignKey(Province, models.DO_NOTHING, db_column='id_province', blank=True, null=True)
    id = models.IntegerField(primary_key=True)

    class Meta:
        db_table = 'municipality'

    def __str__(self):
        return self.denominazione_comune


class BaseMap(models.Model):
    desc_base_map = models.TextField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)

    class Meta:
        db_table = 'base_map'

    def __str__(self):
        return self.desc_base_map


class Physiography(models.Model):
    desc_physiography = models.TextField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)

    class Meta:
        db_table = 'physiography'

    def __str__(self):
        return self.desc_physiography


class PositionalAccuracy(models.Model):
    degree = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    position_type = models.TextField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)

    class Meta:
        db_table = 'positional_accuracy'

    def __str__(self):
        return self.description


class FirstDiscoveryMethod(models.Model):
    desc_first_discovery_method = models.CharField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)

    class Meta:
        db_table = 'first_discovery_method'

    def __str__(self):
        return self.desc_first_discovery_method


class Site(models.Model):
    site_name = models.CharField(max_length=255)
    site_environment_relationship = models.TextField(blank=True, null=True)
    additional_topography = models.TextField(blank=True, null=True)
    elevation = models.IntegerField(blank=True, null=True)
    id_country = models.ForeignKey(Country, models.DO_NOTHING, db_column='id_country', blank=True, null=True)
    id_region = models.ForeignKey(Region, models.DO_NOTHING, db_column='id_region', blank=True, null=True)
    id_province = models.ForeignKey(Province, models.DO_NOTHING, db_column='id_province', blank=True, null=True)
    id_municipality = models.ForeignKey(Municipality, models.DO_NOTHING, db_column='id_municipality', blank=True,
                                        null=True)
    id_physiography = models.ForeignKey(Physiography, on_delete=models.SET_NULL, blank=True, null=True,
                                        db_column='id_physiography')
    id_base_map = models.ForeignKey(BaseMap, on_delete=models.SET_NULL, blank=True, null=True, db_column='id_base_map')
    id_positioning_mode = models.ForeignKey(PositioningMode, on_delete=models.SET_NULL, blank=True, null=True,
                                            db_column='id_positioning_mode')
    id_positional_accuracy = models.ForeignKey(PositionalAccuracy, on_delete=models.SET_NULL, blank=True, null=True,
                                               db_column='id_positional_accuracy')
    id_first_discovery_method = models.ForeignKey(FirstDiscoveryMethod, on_delete=models.SET_NULL, blank=True,
                                                  null=True, db_column='id_first_discovery_method')
    locality_name = models.CharField(max_length=255, blank=True, null=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    lon = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    geometry = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True, db_column='notes')

    class Meta:
        db_table = 'site'

    def __str__(self):
        return f'{self.site_name} - {self.site_environment_relationship} - {self.additional_topography} - {self.elevation} - {self.id_country} - {self.id_region} - {self.id_province} - {self.id_municipality} - {self.id_physiography} - {self.id_base_map} - {self.id_positioning_mode} - {self.id_positional_accuracy} - {self.id_first_discovery_method} - {self.locality_name} - {self.lat} - {self.lon}'


class ArchEvRelatedDoc(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField(blank=True, null=True)
    author = models.TextField(blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    id_archaeological_evidence = models.ForeignKey('ArchaeologicalEvidence', on_delete=models.CASCADE,
                                                   db_column='id_archaeological_evidence', blank=True, null=True)

    class Meta:
        db_table = 'arch_ev_related_doc'

    def __str__(self):
        return f'{self.name} - {self.author} - {self.year} - {self.id_archaeological_evidence}'


class ArchEvResearch(models.Model):
    id_archaeological_evidence = models.ForeignKey('ArchaeologicalEvidence', on_delete=models.CASCADE,
                                                   db_column='id_archaeological_evidence', blank=True, null=True)
    id_research = models.IntegerField()
    id = models.AutoField(primary_key=True)

    class Meta:
        db_table = 'arch_ev_research'

    def __str__(self):
        return f'{self.id_archaeological_evidence} - {self.id_research}'


class ArchEvSources(models.Model):
    id_archaeological_evidence = models.ForeignKey('ArchaeologicalEvidence', on_delete=models.CASCADE,
                                                   db_column='id_archaeological_evidence', blank=True, null=True)
    id_sources = models.ForeignKey('Sources', models.DO_NOTHING, db_column='id_sources')
    id = models.AutoField(primary_key=True)

    class Meta:
        db_table = 'arch_ev_sources'

    def __str__(self):
        return f'{self.id_archaeological_evidence} - {self.id_sources}'


class Chronology(models.Model):
    chronological_period = models.CharField(blank=True, null=True)
    start = models.IntegerField(blank=True, null=True)
    stop = models.IntegerField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)

    class Meta:
        db_table = 'chronology'

    def __str__(self):
        return f'{self.chronological_period} - {self.start} - {self.stop}'


class InvestigationType(models.Model):
    desc_investigation_type = models.TextField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)

    class Meta:
        db_table = 'investigation_type'

    def __str__(self):
        return self.desc_investigation_type


class Investigation(models.Model):
    id = models.AutoField(primary_key=True)
    project_name = models.TextField(blank=True, null=True)
    period = models.TextField(blank=True, null=True)
    id_investigation_type = models.ForeignKey(InvestigationType, on_delete=models.SET_NULL, blank=True, null=True,
                                              db_column='id_investigation_type')

    class Meta:
        db_table = 'investigation'

    def __str__(self):
        return f'{self.project_name} - {self.period}'


class SiteInvestigation(models.Model):
    id_site = models.ForeignKey(Site, on_delete=models.CASCADE, db_column='id_site', blank=True, null=True)
    id_investigation = models.ForeignKey(Investigation, on_delete=models.CASCADE, db_column='id_investigation',
                                         blank=True, null=True)

    class Meta:
        db_table = 'site_investigation'

    def __str__(self):
        return f'{self.id_site} - {self.id_investigation}'


class ArchaeologicalEvidence(models.Model):
    id = models.AutoField(primary_key=True)
    id_archaeological_evidence_typology = models.ForeignKey('ArchaeologicalEvidenceTypology', models.DO_NOTHING,
                                                            blank=True, null=True,
                                                            db_column='id_archaeological_evidence_typology')
    description = models.TextField(blank=True, null=True)
    evidence_name = models.CharField(max_length=255, blank=True, null=True)
    id_country = models.ForeignKey(Country, models.DO_NOTHING, db_column='id_country', blank=True, null=True)
    id_region = models.ForeignKey(Region, models.DO_NOTHING, db_column='id_region', blank=True, null=True)
    id_municipality = models.ForeignKey(Municipality, models.DO_NOTHING, db_column='id_municipality', blank=True, null=True )
    id_physiography = models.ForeignKey(Physiography, models.DO_NOTHING, db_column='id_physiography', blank=True, null=True )
    id_positioning_mode = models.ForeignKey(PositioningMode, models.DO_NOTHING, db_column='id_positioning_mode', )
    id_positional_accuracy = models.ForeignKey(PositionalAccuracy, models.DO_NOTHING,
                                               db_column='id_positional_accuracy', )
    id_base_map = models.ForeignKey(BaseMap, models.DO_NOTHING, db_column='id_base_map', blank=True, null=True)
    id_first_discovery_method = models.ForeignKey(FirstDiscoveryMethod, models.DO_NOTHING,
                                                  db_column='id_first_discovery_method', )
    id_investigation = models.ForeignKey(Investigation, on_delete=models.CASCADE, db_column='id_investigation',
                                         blank=True, null=True)
    elevation = models.IntegerField(blank=True, null=True)
    additional_topography = models.TextField(blank=True, null=True)
    locality_name = models.CharField(blank=True, null=True)
    id_province = models.ForeignKey(Province, models.DO_NOTHING, db_column='id_province', blank=True, null=True)
    lat = models.FloatField(blank=True, null=True)
    lon = models.FloatField(blank=True, null=True)
    id_chronology = models.ForeignKey(Chronology, models.DO_NOTHING, db_column='id_chronology', blank=True, null=True)
    chronology_certainty_level = models.IntegerField(default=1, blank=True, null=True,
                                                     db_column='chronology_certainty_level')
    geometry = models.TextField()
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'archaeological_evidence'

    def __str__(self):
        return f'{self.id}'


class ArchaeologicalEvidenceTypology(models.Model):
    id = models.IntegerField(primary_key=True)
    desc_typology_archaeological_evidence = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'archaeological_evidence_typology'

    def __str__(self):
        return self.desc_typology_archaeological_evidence


class Bibliography(models.Model):
    title = models.CharField(blank=True, null=True)
    author = models.CharField(blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    doi = models.TextField(db_column='DOI', blank=True, null=True)  # Field name made lowercase.
    tipo = models.TextField(blank=True, null=True)
    id = models.AutoField(primary_key=True)

    class Meta:
        db_table = 'bibliography'

    def __str__(self):
        return f'{self.title} - {self.author} - {self.year}'


class FunctionalClass(models.Model):
    desc_functional_class = models.TextField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)

    class Meta:
        db_table = 'functional_class'

    def __str__(self):
        return self.desc_functional_class


class Image(models.Model):
    file_name = models.TextField(blank=True, null=True)
    acquisition_date = models.TextField(blank=True, null=True)
    desc_image = models.TextField(blank=True, null=True)
    id_image_scale = models.IntegerField(blank=True, null=True)
    id_image_type = models.IntegerField(blank=True, null=True)
    id = models.AutoField(primary_key=True)
    id_anagraphic = models.IntegerField(blank=True, null=True)
    format = models.TextField(blank=True, null=True)
    projection = models.TextField(blank=True, null=True)
    spatial_resolution = models.TextField(blank=True, null=True)
    author = models.TextField(blank=True, null=True)
    source_url = models.TextField(blank=True, null=True)
    key_words = models.TextField(blank=True, null=True)
    id_site = models.ForeignKey(Site, on_delete=models.CASCADE, blank=True, null=True, db_column='id_site')
    id_archaeological_evidence = models.ForeignKey('ArchaeologicalEvidence', on_delete=models.CASCADE, blank=True, null=True, db_column='id_archaeological_evidence')

    class Meta:
        db_table = 'image'

    def __str__(self):
        return self.file_name or f"Image {self.id}"


class ImageScale(models.Model):
    desc_image_scale = models.TextField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)

    class Meta:
        db_table = 'image_scale'

    def __str__(self):
        return self.desc_image_scale


class ImageType(models.Model):
    desc_image_type = models.TextField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)

    class Meta:
        db_table = 'image_type'

    def __str__(self):
        return self.desc_image_type


class IntepretationAuthor(models.Model):
    id_interpretation = models.IntegerField(blank=True, null=True)
    id_author = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'intepretation_author'

    def __str__(self):
        return f'{self.id_interpretation} - {self.id_author}'


class Interpretation(models.Model):
    id = models.BigAutoField(primary_key=True)
    id_site = models.ForeignKey(Site, on_delete=models.CASCADE, db_column='id_site', blank=True, null=True)
    id_functional_class = models.ForeignKey('FunctionalClass', on_delete=models.SET_NULL, null=True, blank=True,
                                            db_column='id_functional_class')
    id_typology = models.ForeignKey('Typology', on_delete=models.SET_NULL, null=True, blank=True,
                                    db_column='id_typology')
    id_typology_detail = models.ForeignKey('TypologyDetail', on_delete=models.SET_NULL, null=True, blank=True,
                                           db_column='id_typology_detail')
    notes = models.TextField(blank=True, null=True, db_column='notes')
    id_chronology = models.ForeignKey('Chronology', on_delete=models.SET_NULL, null=True, blank=True,
                                      db_column='id_chronology')
    chronology_certainty_level = models.IntegerField(default=1, blank=True, null=True,
                                                     db_column='chronology_certainty_level')

    class Meta:
        db_table = 'interpretation'
        db_table_comment = 'Qui vengono raccolte le diverse interpretazioni date al sito (in merito alla sua classe funzionale e alla tipologia) proposte dai diversi ricercatori'

    def __str__(self):
        return f'{self.id} - {self.id_site} - {self.id_functional_class} - {self.id_typology} - {self.id_typology_detail}'


class InterpretationBibliography(models.Model):
    id_interpretation = models.ForeignKey(Interpretation, on_delete=models.CASCADE, db_column='id_interpretation',
                                          blank=True, null=True)
    id_bibliography = models.ForeignKey(Bibliography, on_delete=models.CASCADE, db_column='id_bibliography', blank=True,
                                        null=True)

    class Meta:
        db_table = 'interpretation_bibliography'

    def __str__(self):
        return f'{self.id_interpretation} - {self.id_bibliography}'


class Research(models.Model):
    title = models.CharField(blank=True, null=True)
    year = models.CharField(blank=True, null=True, max_length=4)
    keywords = models.CharField(blank=True, null=True)
    abstract = models.TextField(blank=True, null=True)
    type = models.CharField(blank=True, null=True)
    submitted_by = models.ForeignKey(User, blank=True, null=True, on_delete=models.DO_NOTHING, db_column='submitted_by')
    geometry = models.CharField()
    id = models.AutoField(primary_key=True, editable=False)

    class Meta:
        db_table = 'research'

    def __str__(self):
        return f'{self.title} - {self.year} - {self.keywords} - {self.abstract} - {self.type} - {self.geometry}'


class ResearchAuthor(models.Model):
    id_research = models.ForeignKey(Research, on_delete=models.CASCADE, db_column='id_research', blank=True, null=True)
    # id_author now points to User (auth_user table), column is id_author_id in database
    id_author = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, 
                                 related_name='research_authorships')

    class Meta:
        db_table = 'research_author'
        constraints = [
            models.UniqueConstraint(fields=['id_research', 'id_author'], name='unique_research_author_pair')
        ]

    def __str__(self):
        return f'{self.id_research} - {self.id_author}'


class SiteArchEvidence(models.Model):
    id_site = models.ForeignKey('Site', on_delete=models.CASCADE, db_column='id_site')
    id_archaeological_evidence = models.ForeignKey('ArchaeologicalEvidence', on_delete=models.CASCADE,
                                                   db_column='id_archaeological_evidence')
    id = models.AutoField(primary_key=True)

    class Meta:
        db_table = 'site_arch_evidence'
        db_table_comment = 'Tabella che implementa la relazione 0,n a 0,n tra sito e evidenza archeologica.'

    def __str__(self):
        return f'{self.id_site} - {self.id_archaeological_evidence}'


class SiteBibliography(models.Model):
    id_site = models.ForeignKey(Site, on_delete=models.CASCADE, blank=True, null=True, db_column='id_site')
    id_bibliography = models.ForeignKey(Bibliography, on_delete=models.CASCADE, db_column='id_bibliography', blank=True,
                                        null=True)

    class Meta:
        db_table = 'site_bibliography'

    def __str__(self):
        return f'{self.id_site} - {self.id_bibliography}'


class SiteRelatedDocumentation(models.Model):
    name = models.TextField(blank=True, null=True)
    author = models.TextField(blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    id_site = models.ForeignKey(Site, on_delete=models.CASCADE, blank=True, null=True, db_column='id_site')
    id = models.AutoField(primary_key=True)

    class Meta:
        db_table = 'site_related_documentation'

    def __str__(self):
        return f'{self.name} - {self.author} - {self.year} - {self.id_site}'


class SiteResearch(models.Model):
    id = models.AutoField(primary_key=True)
    id_site = models.ForeignKey(Site, on_delete=models.CASCADE, db_column='id_site')
    id_research = models.ForeignKey(Research, on_delete=models.CASCADE, db_column='id_research')

    class Meta:
        db_table = 'site_research'
        constraints = [
            models.UniqueConstraint(fields=['id_site', 'id_research'], name='unique_site_research_pair')
        ]

    def __str__(self):
        return f'{self.id_site} - {self.id_research}'


class Sources(models.Model):
    name = models.TextField(blank=True, null=True)
    id_chronology = models.ForeignKey('Chronology', models.SET_NULL, blank=True, null=True, db_column='id_chronology')
    id_sources_typology = models.ForeignKey('SourcesType', models.SET_NULL, blank=True, null=True,
                                            db_column='id_sources_typology')
    id = models.AutoField(primary_key=True)

    class Meta:
        db_table = 'sources'

    def __str__(self):
        return f'{self.name} - {self.id_chronology} - {self.id_sources_typology}'


class SiteSources(models.Model):
    id_site = models.ForeignKey(Site, on_delete=models.CASCADE, blank=True, null=True, db_column='id_site')
    id_sources = models.ForeignKey(Sources, on_delete=models.CASCADE, db_column='id_sources')

    class Meta:
        db_table = 'site_sources'

    def __str__(self):
        return f'{self.id_site} - {self.id_sources}'


class SiteToponymy(models.Model):
    ancient_place_name = models.TextField(blank=True, null=True)
    contemporary_place_name = models.TextField(blank=True, null=True)
    id_site = models.ForeignKey(Site, on_delete=models.CASCADE, blank=True, null=True, db_column='id_site')

    class Meta:
        db_table = 'site_toponymy'

    def __str__(self):
        return f'{self.ancient_place_name} - {self.contemporary_place_name} - {self.id_site}'


class SourcesType(models.Model):
    desc_sources_type = models.TextField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)

    class Meta:
        db_table = 'sources_type'

    def __str__(self):
        return self.desc_sources_type


class Typology(models.Model):
    id = models.IntegerField(primary_key=True)
    desc_typology = models.TextField(blank=True, null=True)
    id_functional_class = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'typology'
        db_table_comment = 'tabella relativa alle tipologie di sito associate alle classi funzionali principali'

    def __str__(self):
        return self.desc_typology


class TypologyDetail(models.Model):
    id = models.IntegerField(primary_key=True)
    desc_typology_detail = models.TextField(blank=True, null=True)
    id_typology = models.IntegerField(blank=True, null=True)
    id_functional_class = models.ForeignKey('FunctionalClass', models.SET_NULL, db_column='id_functional_class',
                                            blank=True, null=True)

    class Meta:
        db_table = 'typology_detail'

    def __str__(self):
        return self.desc_typology_detail
