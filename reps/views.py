from django.shortcuts import render
from django.db.models import Prefetch
from django.utils.safestring import mark_safe
import json
from django.core.serializers.json import DjangoJSONEncoder
from .models import Area, Branch, Representative

DISTRICT_DISTRIBUTION = [
    ("suva", "Suva", 80),
    ("nausori", "Nausori", 119),
    ("nadi", "Nadi", 33),
    ("nadroga-navosa", "Nadroga/Navosa", 63),
    ("lautoka-yasawa", "Lautoka/Yasawa", 52),
    ("ba", "Ba", 43),
    ("tavua-vatukoula-nadarivatu", "Tavua/Vatukoula/Nadarivatu", 19),
    ("rakiraki", "Rakiraki", 43),
    ("macuata", "Macuata", 71),
    ("bua", "Bua", 29),
    ("cakaudrove", "Cakaudrove", 66),
    ("eastern", "Eastern", 117),
]


class _EmptyRelation:
    def all(self):
        return []


class DistrictArea:
    branches = _EmptyRelation()
    reps = _EmptyRelation()

    def __init__(self, slug, name, hos_count):
        self.id = slug
        self.slug = slug
        self.name = name
        self.hos_count = hos_count
        self.summary = f"{hos_count} Heads of Schools recorded in the current FPSPA district distribution."


def _district_areas():
    return [DistrictArea(slug, name, hos_count) for slug, name, hos_count in DISTRICT_DISTRIBUTION]


def reps_list(request):
    reps = Representative.objects.select_related('area', 'branch').all()
    return render(request, 'reps/reps_list.html', {'reps': reps})

def areas(request):
    areas = _district_areas()

    # Prepare JSON-safe data for branches (for maps/modals)
    branches_data = []
    branches_data = []

    context = {
        'areas': areas,
        'branches_json': json.dumps(branches_data, cls=DjangoJSONEncoder)
    }

    return render(request, 'reps/areas.html', context)



def areas_list(request):
    areas = _district_areas()

    # Build branches JSON for map markers (only branches with coords)
    branches_data = []
    branches_data = []

    context = {
        'areas': areas,
        'branches_json': mark_safe(json.dumps(branches_data)),
    }
    return render(request, 'representatives/areas_modals.html', context)
