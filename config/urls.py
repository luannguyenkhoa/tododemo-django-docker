# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.conf.urls import url, include
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from tastypie.api import Api
# from django.views.generic import TemplateView
from django.views import defaults as default_views

from backend.task.api import TaskResource
from backend.account.api import AuthenticationResource, UserProfileResource, UserResource

v1_api = Api(api_name='v1')
v1_api.register(UserProfileResource())
v1_api.register(AuthenticationResource())
v1_api.register(UserResource())
v1_api.register(TaskResource())

urlpatterns = [

    # Django Admin, use {% url 'admin:index' %}
    url(settings.ADMIN_URL, include(admin.site.urls)),

    # User management
    url(r'^api/', include(v1_api.urls)),
    url(r'^accounts/', include('allauth.urls')),

    # Your stuff: custom urls includes go here


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    import debug_toolbar
    urlpatterns += [
        url(r'^400/$', default_views.bad_request, kwargs={'exception': Exception("Bad Request!")}),
        url(r'^403/$', default_views.permission_denied, kwargs={'exception': Exception("Permissin Denied")}),
        url(r'^404/$', default_views.page_not_found, kwargs={'exception': Exception("Page not Found")}),
        url(r'^500/$', default_views.server_error),
        url(r'^__debug__', include(debug_toolbar.urls)),
    ]
