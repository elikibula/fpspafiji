from django.shortcuts import render

from .models import LiveStream


def live(request):
    published = LiveStream.objects.filter(is_published=True)
    featured_stream = published.filter(is_featured=True).order_by(
        '-is_live', '-event_date', '-created_at'
    ).first()
    previous_streams = published.exclude(pk=featured_stream.pk) if featured_stream else published
    return render(request, 'livestream/live.html', {
        'featured_stream': featured_stream,
        'previous_streams': previous_streams.order_by('-event_date', '-created_at'),
    })
