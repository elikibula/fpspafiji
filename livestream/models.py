from urllib.parse import parse_qs, quote, urlparse

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


class LiveStream(models.Model):
    YOUTUBE = 'youtube'
    FACEBOOK = 'facebook'
    PLATFORM_CHOICES = ((YOUTUBE, 'YouTube'), (FACEBOOK, 'Facebook'))

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    stream_url = models.URLField(max_length=500)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, editable=False)
    event_date = models.DateTimeField(null=True, blank=True)
    is_live = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    thumbnail = models.ImageField(upload_to='livestream/thumbnails/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-event_date', '-created_at')

    def __str__(self):
        return self.title

    def _parsed_url(self):
        return urlparse((self.stream_url or '').strip())

    def detect_platform(self):
        parsed = self._parsed_url()
        hostname = (parsed.hostname or '').lower().rstrip('.')
        if parsed.scheme not in ('http', 'https'):
            raise ValidationError('Please enter a valid YouTube or Facebook livestream URL.')
        if hostname == 'youtu.be' or hostname.endswith('.youtu.be') or hostname == 'youtube.com' or hostname.endswith('.youtube.com'):
            return self.YOUTUBE
        if hostname == 'facebook.com' or hostname.endswith('.facebook.com'):
            return self.FACEBOOK
        raise ValidationError('Please enter a valid YouTube or Facebook livestream URL.')

    @property
    def youtube_video_id(self):
        if not self.stream_url:
            return None
        parsed = self._parsed_url()
        hostname = (parsed.hostname or '').lower().rstrip('.')
        video_id = None
        if hostname == 'youtu.be' or hostname.endswith('.youtu.be'):
            video_id = parsed.path.strip('/').split('/')[0]
        elif hostname == 'youtube.com' or hostname.endswith('.youtube.com'):
            path_parts = [part for part in parsed.path.split('/') if part]
            if parsed.path.rstrip('/') == '/watch':
                video_id = parse_qs(parsed.query).get('v', [None])[0]
            elif len(path_parts) >= 2 and path_parts[0] in ('live', 'embed'):
                video_id = path_parts[1]
        if video_id and all(character.isalnum() or character in '_-' for character in video_id):
            return video_id
        return None

    @property
    def embed_url(self):
        if self.platform == self.YOUTUBE:
            video_id = self.youtube_video_id
            return f'https://www.youtube.com/embed/{video_id}?controls=1' if video_id else ''
        if self.platform == self.FACEBOOK and self.stream_url:
            encoded_url = quote(self.stream_url.strip(), safe='')
            return f'https://www.facebook.com/plugins/video.php?href={encoded_url}&show_text=false&width=1280'
        return ''

    @property
    def facebook_share_url(self):
        if not self.stream_url:
            return ''
        encoded_url = quote(self.stream_url.strip(), safe='')
        return f'https://www.facebook.com/sharer/sharer.php?u={encoded_url}'

    @property
    def display_thumbnail_url(self):
        if self.thumbnail:
            return self.thumbnail.url
        if self.platform == self.YOUTUBE and self.youtube_video_id:
            return f'https://img.youtube.com/vi/{self.youtube_video_id}/hqdefault.jpg'
        return ''

    @property
    def homepage_cta_label(self):
        if self.is_live:
            return 'Watch Live Now'
        if self.event_date and self.event_date < timezone.now():
            return 'Watch Conference Recording'
        return 'View 2026 Conference Livestream'

    def clean(self):
        super().clean()
        self.stream_url = (self.stream_url or '').strip()
        try:
            self.platform = self.detect_platform()
        except ValidationError as error:
            raise ValidationError({'stream_url': error.messages}) from error
        if self.platform == self.YOUTUBE and not self.youtube_video_id:
            raise ValidationError({'stream_url': 'Please enter a YouTube URL containing a valid video ID.'})
        if self.platform == self.FACEBOOK and not self._parsed_url().path.strip('/') and not self._parsed_url().query:
            raise ValidationError({'stream_url': 'Please enter a valid Facebook video or livestream URL.'})
        if self.is_live and not self.is_published:
            raise ValidationError({'is_published': 'A stream marked live must also be published.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        with transaction.atomic():
            if self.is_featured:
                type(self).objects.select_for_update().filter(is_featured=True).exclude(pk=self.pk).update(is_featured=False)
            return super().save(*args, **kwargs)
