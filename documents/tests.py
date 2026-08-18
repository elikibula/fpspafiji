from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Document, DocumentCategory
from .forms import DocumentForm


class PublicDocumentsTests(TestCase):
    def setUp(self):
        self.override = override_settings(
            SECURE_SSL_REDIRECT=False,
            STORAGES={
                'default': {'BACKEND': 'django.core.files.storage.InMemoryStorage'},
                'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
            },
        )
        self.override.enable()
        self.user = get_user_model().objects.create_user(
            username='uploader', password='test', role='staff'
        )
        self.public_category = DocumentCategory.objects.create(name='Public Documents', is_public=True)
        self.private_category = DocumentCategory.objects.create(name='Private Documents')
        self.public_document = self._document('Public file', self.public_category, b'public')
        self.private_document = self._document('Private file', self.private_category, b'private')

    def tearDown(self):
        self.override.disable()

    def _document(self, title, category, content):
        return Document.objects.create(
            title=title,
            file=SimpleUploadedFile(f'{title}.txt', content),
            category=category,
            subcategory=None,
            author=self.user,
            owner=self.user,
        )

    def test_resources_only_lists_documents_from_public_folders(self):
        response = self.client.get(reverse('resources'))
        self.assertContains(response, 'Public file')
        self.assertNotContains(response, 'Private file')

    def test_public_download_rejects_private_document(self):
        public_url = reverse('documents:public_document_download', args=[self.public_document.pk])
        private_url = reverse('documents:public_document_download', args=[self.private_document.pk])
        self.assertEqual(self.client.get(public_url).status_code, 200)
        self.assertEqual(self.client.get(private_url).status_code, 404)

    def test_public_document_form_does_not_require_subcategory(self):
        form = DocumentForm(data={
            'title': 'Public notice',
            'description': 'A public notice',
            'category': self.public_category.pk,
        })
        form.is_valid()
        self.assertNotIn('subcategory', form.errors)

    def test_private_document_form_still_requires_subcategory(self):
        form = DocumentForm(data={
            'title': 'Private notice',
            'description': 'A private notice',
            'category': self.private_category.pk,
        })
        form.is_valid()
        self.assertIn('subcategory', form.errors)

    def test_uploader_can_open_public_category_without_group_assignment(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('documents:category_detail', args=[self.public_category.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Public file')

    def test_document_detail_renders_without_subcategory(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('documents:document_detail', args=[self.public_document.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Subcategory:')
        self.assertContains(response, 'None')
        self.assertContains(response, 'Back to Public Resources')

    def test_view_and_preview_pages_render(self):
        self.client.force_login(self.user)
        for route_name in ('document_view', 'document_preview'):
            response = self.client.get(
                reverse(f'documents:{route_name}', args=[self.public_document.pk])
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, self.public_document.title)

    def test_inline_document_streams_in_browser(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('documents:document_inline', args=[self.public_document.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('inline', response.headers['Content-Disposition'])

    def test_document_form_accepts_files_up_to_80_mb(self):
        uploaded = SimpleUploadedFile('allowed.pdf', b'content', content_type='application/pdf')
        uploaded.size = DocumentForm.MAX_FILE_SIZE
        form = DocumentForm(
            data={
                'title': 'Allowed public file',
                'description': 'At the upload limit',
                'category': self.public_category.pk,
            },
            files={'file': uploaded},
        )
        form.is_valid()
        self.assertNotIn('file', form.errors)

    def test_document_form_rejects_files_over_80_mb(self):
        uploaded = SimpleUploadedFile('too-large.pdf', b'content', content_type='application/pdf')
        uploaded.size = DocumentForm.MAX_FILE_SIZE + 1
        form = DocumentForm(
            data={
                'title': 'Oversized public file',
                'description': 'Over the upload limit',
                'category': self.public_category.pk,
            },
            files={'file': uploaded},
        )
        form.is_valid()
        self.assertIn('file', form.errors)
        self.assertIn('maximum upload size is 80 MB', form.errors['file'][0])

# Create your tests here.
