"""
URL configuration for rustdesk_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import logging

from django.urls import path, include

from common.env import PublicConfig
from rustdesk_api.settings import INTERNAL_IPS

logger = logging.getLogger(__name__)

urlpatterns = [
    path('', include('apps.web.urls')),
    path('api/', include('apps.client_apis.urls')),
]

if PublicConfig.DEBUG:
    import debug_toolbar

    urlpatterns = [
                      path('__debug__/', include(debug_toolbar.urls)),
                  ] + urlpatterns
    logger.debug("[django] debug toolbar enabled.")
    logger.debug(f"[django] debug toolbar internal IPs: {INTERNAL_IPS}.")
