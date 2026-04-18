from django import forms
from .models import Research, Site, ArchaeologicalEvidence, FunctionalClass, Typology, TypologyDetail, Chronology, \
    InvestigationType, SourcesType, ImageType, ImageScale, SiteToponymy, PositioningMode, PositionalAccuracy, \
    FirstDiscoveryMethod
from django.contrib.gis.geos import Point

class ResearchForm(forms.ModelForm):
    class Meta:
        model = Research
        fields = ['title', 'year', 'keywords', 'abstract', 'type', 'geometry']
        widgets = {

            'geometry': forms.TextInput(attrs={
                'id': 'geometry',
                'readonly': 'readonly',
                'rows': 4,
                'class': 'form-control'
            })
        }

    def clean_geometry(self):
        geometry = self.cleaned_data.get('geometry')
        if geometry and not geometry.startswith('(('):
            raise forms.ValidationError("Il campo geometria deve essere nel formato ((x,y),(x,y),...)")
        return geometry

CHRONOLOGY_CERTAINTY_CHOICES = [
    (1, 'Incerta'),
    (2, 'Probabile'),
    (3, 'Certa')
]

class SiteForm(forms.ModelForm):
    # Fields from SiteToponymy
    ancient_place_name = forms.CharField(
        max_length=255,
        required=False,
        label="Antichi")

    contemporary_place_name = forms.CharField(
        max_length=255,
        required=False,
        label="Contemporanei")

    functional_class = forms.ModelChoiceField(
        queryset=FunctionalClass.objects.all(),
        required=True,
        label="Classe Funzionale"
    )
    typology = forms.ModelChoiceField(
        queryset=Typology.objects.none(),
        required=False,
        label="Tipologia"
    )
    typology_detail = forms.ModelChoiceField(
        queryset=TypologyDetail.objects.none(),
        required=False,
        label="Sottotipologia"
    )
    chronology = forms.ModelChoiceField(
        queryset=Chronology.objects.all(),
        required=True,
        label="Cronologia"
    )

    chronology_certainty_level = forms.ChoiceField(
        choices=CHRONOLOGY_CERTAINTY_CHOICES,
        required=False,
        label="Grado di certezza della cronologia proposta",
    )

    project_name = forms.CharField(
        max_length=255,
        required=False,
        label="Nome del progetto")

    investigation_type = forms.ModelChoiceField(
        queryset=InvestigationType.objects.all(),
        required=False,
        label="Tipo di indagine")

    periodo = forms.CharField(
        max_length=255,
        required=False,
        label="Periodo")

    title = forms.CharField(
        max_length=255,
        required=False,
        label="Titolo")

    author = forms.CharField(
        max_length=255,
        required=False,
        label="Autore")

    year = forms.IntegerField(
        required=False,
        label="Anno")

    doi = forms.CharField(
        max_length=255,
        required=False,
        label="DOI")

    tipo = forms.CharField(
        max_length=255,
        required=False,
        label="Tipo")

    name = forms.CharField(
        max_length=255,
        required=False,
        label="Name")

    documentation_chronology = forms.ModelChoiceField(
        queryset=Chronology.objects.all(),
        required=False,
        label="Cronologia")

    source_type = forms.ModelChoiceField(
        queryset=SourcesType.objects.all(),
        required=False,
        label="Tipologia di fonte")

    documentation_name = forms.CharField(
        max_length=255,
        required=False,
        label="Nome")

    documentation_author = forms.CharField(
        max_length=255,
        required=False,
        label="Autore")

    documentation_year = forms.IntegerField(
        required=False,
        label="Anno")

    image_type = forms.ModelChoiceField(
        queryset=ImageType.objects.all(),
        required=False,
        label="Tipologia"
    )

    image_scale = forms.ModelChoiceField(
        queryset=ImageScale.objects.all(),
        required=False,
        label="Scala"
    )

    class Meta:
        model = Site
        fields = [
            'site_name', 'site_environment_relationship', 'additional_topography',
            'elevation', 'locality_name', 'lat', 'lon', 'geometry',
            'id_country', 'id_region', 'id_province', 'id_municipality',
            'id_physiography', 'id_base_map', 'id_positioning_mode',
            'id_positional_accuracy', 'id_first_discovery_method', 'description', 'notes'
        ]
        labels = {
            'site_name': 'Nome del sito',
            'site_environment_relationship': 'Rapporto sito-ambiente',
            'additional_topography': 'Riferimenti topografici',
            'elevation': 'Quota',
            'locality_name': 'Locality Name',
            'lat': 'Latitude',
            'lon': 'Longitude',
            'geometry': 'Geometry',
            'id_country': 'Paese',
            'id_region': 'Regione',
            'id_province': 'Provincia',
            'id_municipality': 'Comune',
            'id_physiography': 'Fisiografia',
            'id_base_map': 'Base Cartografica',
            'id_positioning_mode': 'Modalità di Posizionamento',
            'id_positional_accuracy': 'Qualità del Posizionamento',
            'id_first_discovery_method': 'Modalità di rinvenimento (prima scoperta)',
            'description': 'Descrizione',
            'notes': 'Note',
        }

        widgets = {
            'geometry': forms.Textarea(attrs={
                'readonly': 'readonly',
                'rows': 4,
                'class': 'form-control'
            })
        }

    def clean_geometry(self):
        geometry = self.cleaned_data.get('geometry')
        lat = self.cleaned_data.get('lat')
        lon = self.cleaned_data.get('lon')

        if geometry and geometry.strip() != '':
            return geometry  # Already a valid WKT string

        if lat is not None and lon is not None:
            return (float(lon), float(lat))  # Note: GeoDjango uses (x, y) = (lon, lat)

        return None

    def __init__(self, *args, **kwargs):
        super(SiteForm, self).__init__(*args, **kwargs)

        # Style all fields
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

        # Set default country to Italy (id 113)
        if not self.initial.get('id_country') and not self.data.get('id_country'):
            self.fields['id_country'].initial = 113

        # Dynamic Typology options depending on Functional Class selected
        # Check both form data (on submit) and initial values (on prefilling)
        functional_class_id = None
        if 'functional_class' in self.data:
            try:
                functional_class_id = int(self.data.get('functional_class'))
            except (ValueError, TypeError):
                pass
        elif 'functional_class' in self.initial and self.initial['functional_class']:
            # Handle when prefilling - functional_class might be a model instance
            fc = self.initial['functional_class']
            functional_class_id = fc.id if hasattr(fc, 'id') else fc
        
        if functional_class_id:
            self.fields['typology'].queryset = Typology.objects.filter(id_functional_class=functional_class_id)
        elif 'typology' in self.initial and self.initial['typology']:
            # If typology is already set in initial, allow it to be selected
            typology = self.initial['typology']
            typology_id = typology.id if hasattr(typology, 'id') else typology
            if typology_id:
                # Get the functional_class from the typology to set the queryset
                try:
                    typology_obj = Typology.objects.get(id=typology_id)
                    self.fields['typology'].queryset = Typology.objects.filter(id_functional_class=typology_obj.id_functional_class_id)
                except Typology.DoesNotExist:
                    self.fields['typology'].queryset = Typology.objects.none()
        else:
            self.fields['typology'].queryset = Typology.objects.none()

        # Dynamic TypologyDetail options depending on Typology selected
        # Check both form data (on submit) and initial values (on prefilling)
        typology_id = None
        if 'typology' in self.data:
            try:
                typology_id = int(self.data.get('typology'))
            except (ValueError, TypeError):
                pass
        elif 'typology' in self.initial and self.initial['typology']:
            # Handle when prefilling - typology might be a model instance
            typology = self.initial['typology']
            typology_id = typology.id if hasattr(typology, 'id') else typology
        
        if typology_id:
            self.fields['typology_detail'].queryset = TypologyDetail.objects.filter(id_typology=typology_id)
        elif 'typology_detail' in self.initial and self.initial['typology_detail']:
            # If typology_detail is already set in initial, allow it to be selected
            typology_detail = self.initial['typology_detail']
            typology_detail_id = typology_detail.id if hasattr(typology_detail, 'id') else typology_detail
            if typology_detail_id:
                # Get the typology from the typology_detail to set the queryset
                try:
                    typology_detail_obj = TypologyDetail.objects.get(id=typology_detail_id)
                    self.fields['typology_detail'].queryset = TypologyDetail.objects.filter(id_typology=typology_detail_obj.id_typology_id)
                except TypologyDetail.DoesNotExist:
                    self.fields['typology_detail'].queryset = TypologyDetail.objects.none()
        else:
            self.fields['typology_detail'].queryset = TypologyDetail.objects.none()


class ArchaeologicalEvidenceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Style all fields
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        # Set default country to Italy (id 113)
        if not self.initial.get('id_country') and not self.data.get('id_country'):
            self.fields['id_country'].initial = 113

    # These FK fields are required in the model (no blank=True, null=True)
    id_positioning_mode = forms.ModelChoiceField(
        queryset=PositioningMode.objects.all(),
        required=True,
        label="Modalità di Posizionamento"
    )
    
    id_positional_accuracy = forms.ModelChoiceField(
        queryset=PositionalAccuracy.objects.all(),
        required=True,
        label="Qualità del Posizionamento"
    )
    
    id_first_discovery_method = forms.ModelChoiceField(
        queryset=FirstDiscoveryMethod.objects.all(),
        required=False,
        empty_label="---------",
        label="Modalità di rinvenimento (prima scoperta)"
    )
    
    # Geometry field - optional since it's filled via map interaction
    geometry = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        label="Geometry"
    )

    project_name = forms.CharField(
        max_length=255,
        required=False,
        label="Nome del progetto"
    )

    investigation_type = forms.ModelChoiceField(
        queryset=InvestigationType.objects.all(),
        required=False,
        label="Tipo di indagine"
    )

    periodo = forms.CharField(
        max_length=255,
        required=False,
        label="Periodo")

    title = forms.CharField(
        max_length=255,
        required=False,
        label="Titolo")

    author = forms.CharField(
        max_length=255,
        required=False,
        label="Autore")

    year = forms.IntegerField(
        required=False,
        label="Anno")

    doi = forms.CharField(
        max_length=255,
        required=False,
        label="DOI")

    tipo = forms.CharField(
        max_length=255,
        required=False,
        label="Tipo")

    name = forms.CharField(
        max_length=255,
        required=False,
        label="Name")

    documentation_chronology = forms.ModelChoiceField(
        queryset=Chronology.objects.all(),
        required=False,
        label="Cronologia")

    source_type = forms.ModelChoiceField(
        queryset=SourcesType.objects.all(),
        required=False,
        label="Tipologia di fonte")

    documentation_name = forms.CharField(
        max_length=255,
        required=False,
        label="Nome")

    documentation_author = forms.CharField(
        max_length=255,
        required=False,
        label="Autore")

    documentation_year = forms.IntegerField(
        required=False,
        label="Anno")

    image_type = forms.ModelChoiceField(
        queryset=ImageType.objects.all(),
        required=False,
        label="Tipologia"
    )

    image_scale = forms.ModelChoiceField(
        queryset=ImageScale.objects.all(),
        required=False,
        label="Scala"
    )

    class Meta:
        model = ArchaeologicalEvidence
        fields = [
            'id_archaeological_evidence_typology',
            'evidence_name',
            'description',
            'id_country',
            'id_region',
            'id_province',
            'id_municipality',
            'id_physiography',
            'id_positioning_mode',
            'id_positional_accuracy',
            'id_base_map',
            'id_first_discovery_method',
            'id_investigation',
            'elevation',
            'additional_topography',
            'locality_name',
            'lat',
            'lon',
            'geometry',
            'chronology_certainty_level',
            'id_chronology',
            'notes'
        ]

        labels = {
            'id_archaeological_evidence_typology': 'Typology',
            'evidence_name': 'Evidence Name',
            'description': 'Description',
            'id_country': 'Country',
            'id_region': 'Region',
            'id_province': 'Province',
            'id_municipality': 'Municipality',
            'id_physiography': 'Physiography',
            'id_positioning_mode': 'Positioning Mode',
            'id_positional_accuracy': 'Positional Accuracy',
            'id_base_map': 'Base Map',
            'id_first_discovery_method': 'Discovery Method',
            'id_investigation': 'Investigation',
            'elevation': 'Elevation (m)',
            'additional_topography': 'Additional Topography Notes',
            'locality_name': 'Locality Name',
            'lat': 'Latitude',
            'lon': 'Longitude',
            'geometry': 'Geometry',
            'chronology_certainty_level': 'Chronology Certainty Level',
            'id_chronology': 'Chronology',
            'notes': 'Note'
        }

        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'additional_topography': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'geometry': forms.TextInput(attrs={
                'id': 'geometry',
                'readonly': 'readonly',
                'rows': 4,
                'class': 'form-control'
            }),
            'lat': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}),
            'lon': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}),
            'elevation': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}),
        }

    def clean_geometry(self):
        geometry = self.cleaned_data.get('geometry')
        # Return None if empty string to avoid "invalid input syntax for type polygon: ''" error
        if not geometry or geometry.strip() == '':
            return None
        if geometry and not geometry.startswith('(('):
            raise forms.ValidationError("Il campo geometria deve essere nel formato ((x,y),(x,y),...)")
        return geometry
