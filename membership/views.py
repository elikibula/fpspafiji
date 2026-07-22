# membership/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from datetime import date
import uuid
from .models import Member, School
from events.models import Event
from django.utils import timezone
from datetime import date
from django.db import IntegrityError
from django.db import transaction
from django.contrib.auth.models import User
from allauth.account.views import SignupView




def registration_success(request):
    return render(request, 'membership/registration_success.html')

@login_required
def member_dashboard(request):
    try:
        member = Member.objects.get(user=request.user)

        # Get upcoming events (use 'start' instead of 'date')
        upcoming_events = Event.objects.filter(start__gte=timezone.now()).order_by('start')[:5]

       

        context = {
            'member': member,
            'years_of_service': member.years_of_service_display,
            'upcoming_events': upcoming_events,
            
        }
        return render(request, 'membership/dashboard.html', context)

    except Member.DoesNotExist:
        messages.info(request, 'Please complete your membership registration.')
        return redirect('membership:register')

@login_required
def member_profile(request):
    try:
        member = Member.objects.get(user=request.user)
        if request.method == 'POST':
            # Handle profile updates here
            pass
        return render(request, 'membership/profile.html', {'member': member})
    except Member.DoesNotExist:
        return redirect('membership:register')
