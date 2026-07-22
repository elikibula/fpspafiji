from django.db.models import Prefetch
from django.shortcuts import render

from .models import District, DistrictRepresentative


def district_representatives(request):
    representatives = DistrictRepresentative.objects.filter(is_active=True).order_by("order", "name")
    districts = District.objects.filter(is_active=True).prefetch_related(
        Prefetch("representatives", queryset=representatives, to_attr="active_representatives")
    ).order_by("order", "name")
    return render(request, "reps/district_representatives.html", {"districts": districts})


# Backwards-compatible view aliases.
areas = district_representatives
reps_list = district_representatives
