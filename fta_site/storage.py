from django.conf import settings
from django.core.files.storage import FileSystemStorage


class CKEditor5MediaStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("location", settings.MEDIA_ROOT / "uploads" / "ckeditor5")
        kwargs.setdefault("base_url", f"{settings.MEDIA_URL}uploads/ckeditor5/")
        super().__init__(*args, **kwargs)
