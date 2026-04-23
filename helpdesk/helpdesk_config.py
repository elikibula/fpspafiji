# helpdesk_config.py
from django.conf import settings
from django.contrib.auth import get_user_model

class CustomHelpdeskConfig:
    @staticmethod
    def get_user_model():
        return get_user_model()

# In settings.py
HELPDESK_CONFIG = 'myapp.helpdesk_config.CustomHelpdeskConfig'