from urllib.parse import quote

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import LiveStream


class LiveStreamModelTests(TestCase):
    def make_stream(self, **overrides):
        values = {'title': 'FHTA Conference', 'stream_url': 'https://www.youtube.com/watch?v=ABC123'}
        values.update(overrides)
        return LiveStream.objects.create(**values)

    def test_youtube_watch_url_detected(self):
        stream = self.make_stream()
        self.assertEqual(stream.platform, LiveStream.YOUTUBE)

    def test_youtu_be_url_detected(self):
        stream = self.make_stream(stream_url='https://youtu.be/ABC123?si=share')
        self.assertEqual(stream.platform, LiveStream.YOUTUBE)
        self.assertEqual(stream.youtube_video_id, 'ABC123')

    def test_youtube_live_url_detected(self):
        stream = self.make_stream(stream_url='https://www.youtube.com/live/ABC123?feature=shared')
        self.assertEqual(stream.platform, LiveStream.YOUTUBE)
        self.assertEqual(stream.youtube_video_id, 'ABC123')

    def test_facebook_url_detected(self):
        stream = self.make_stream(stream_url='https://www.facebook.com/FHTA/videos/123456789/')
        self.assertEqual(stream.platform, LiveStream.FACEBOOK)

    def test_invalid_provider_rejected(self):
        with self.assertRaisesMessage(ValidationError, 'Please enter a valid YouTube or Facebook livestream URL.'):
            self.make_stream(stream_url='https://example.com/video/ABC123')

    def test_youtube_embed_url(self):
        stream = self.make_stream(stream_url='https://www.youtube.com/watch?v=ABC123&t=10&feature=shared')
        self.assertEqual(stream.embed_url, 'https://www.youtube.com/embed/ABC123?controls=1')

    def test_facebook_share_url(self):
        url = 'https://www.youtube.com/watch?v=ABC123'
        stream = self.make_stream(stream_url=url)
        self.assertEqual(stream.facebook_share_url, f'https://www.facebook.com/sharer/sharer.php?u={quote(url, safe="")}')

    def test_facebook_embed_url(self):
        url = 'https://www.facebook.com/watch/?v=123456789'
        stream = self.make_stream(stream_url=url)
        self.assertEqual(stream.embed_url, f'https://www.facebook.com/plugins/video.php?href={quote(url, safe="")}&show_text=false&width=1280')

    def test_only_one_featured_stream_remains(self):
        first = self.make_stream(is_featured=True)
        second = self.make_stream(title='Second', stream_url='https://youtu.be/SECOND2', is_featured=True)
        first.refresh_from_db()
        self.assertFalse(first.is_featured)
        self.assertTrue(second.is_featured)


class LiveStreamViewTests(TestCase):
    def make_stream(self, **overrides):
        values = {'title': 'Featured Conference', 'stream_url': 'https://youtu.be/FEATURE1'}
        values.update(overrides)
        return LiveStream.objects.create(**values)

    def test_page_returns_200_without_records(self):
        response = self.client.get(reverse('livestream:live'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No livestream is currently scheduled')

    def test_page_displays_featured_stream(self):
        self.make_stream(is_featured=True)
        response = self.client.get(reverse('livestream:live'))
        self.assertContains(response, 'Featured Conference')
        self.assertContains(response, 'https://www.youtube.com/embed/FEATURE1?controls=1')
        self.assertContains(response, 'Share on Facebook')
        self.assertContains(response, 'referrerpolicy="strict-origin-when-cross-origin"')
        self.assertEqual(response.headers['Referrer-Policy'], 'strict-origin-when-cross-origin')

    def test_unpublished_streams_are_not_public(self):
        self.make_stream(title='Hidden broadcast', is_published=False)
        response = self.client.get(reverse('livestream:live'))
        self.assertNotContains(response, 'Hidden broadcast')

    def test_previous_streams_exclude_featured(self):
        featured = self.make_stream(is_featured=True)
        previous = self.make_stream(title='Previous Broadcast', stream_url='https://youtu.be/PREVIOUS1')
        response = self.client.get(reverse('livestream:live'))
        self.assertEqual(response.context['featured_stream'], featured)
        self.assertQuerySetEqual(response.context['previous_streams'], [previous])

    def test_homepage_works_without_livestream(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['live_stream'])
        self.assertContains(response, 'View Livestreams')
        self.assertContains(response, reverse('livestream:live'))

    def test_homepage_receives_featured_livestream(self):
        stream = self.make_stream(is_featured=True)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['live_stream'], stream)
        self.assertContains(response, 'View 2026 Conference Livestream')
