from django.core.management import execute_from_command_line
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ShareLand.settings')

import django
django.setup()

from frontend.models import ArchaeologicalEvidence
ev = ArchaeologicalEvidence.objects.get(id=50)
print(f"Evidence ID 50: {ev.evidence_name}")
print(f"Description: {ev.description}")
print(f"ID Country: {ev.id_country}")
