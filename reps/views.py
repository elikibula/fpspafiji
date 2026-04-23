from django.shortcuts import render
from django.db.models import Prefetch
from django.utils.safestring import mark_safe
import json
from django.core.serializers.json import DjangoJSONEncoder
from .models import Area, Branch, Representative

def reps_list(request):
    reps = Representative.objects.select_related('area', 'branch').all()
    return render(request, 'reps/reps_list.html', {'reps': reps})

def areas(request):
    # Fetch all areas
    areas = Area.objects.prefetch_related('branches', 'reps').all()

    # Prepare JSON-safe data for branches (for maps/modals)
    branches_data = []
    for branch in Branch.objects.all():
        branches_data.append({
            'id': branch.id,
            'name': branch.name,
            'address': branch.address or '',
            'lat': float(branch.latitude) if branch.latitude else None,
            'lng': float(branch.longitude) if branch.longitude else None,
            'area_id': branch.area.id if branch.area else None,
            'reps': [
                {
                    'name': rep.name,
                    'role': rep.role,
                    'phone': rep.phone,
                    'email': rep.email,
                }
                for rep in branch.reps.all()

            ],
        })

    context = {
        'areas': areas,
        'branches_json': json.dumps(branches_data, cls=DjangoJSONEncoder)
    }

    return render(request, 'reps/areas.html', context)



def areas_list(request):
    # Prefetch branches + reps for each area to minimize queries
    areas = Area.objects.prefetch_related(
        Prefetch('branches', queryset=Branch.objects.prefetch_related('reps'))
    ).all()

    # Build branches JSON for map markers (only branches with coords)
    branches_data = []
    for area in areas:
        for branch in area.branches.all():
            if branch.latitude is None or branch.longitude is None:
                continue
            reps = []
            for rep in branch.reps.all():
                reps.append({
                    'name': rep.name,
                    'role': rep.role,
                    'phone': rep.phone,
                    'email': rep.email,
                })
            branches_data.append({
                'id': branch.id,
                'name': branch.name,
                'address': branch.address,
                'lat': float(branch.latitude),
                'lng': float(branch.longitude),
                'area_id': area.id,
                'area_name': area.name,
                'reps': reps,
            })

    context = {
        'areas': areas,
        'branches_json': mark_safe(json.dumps(branches_data)),
    }
    return render(request, 'representatives/areas_modals.html', context)
