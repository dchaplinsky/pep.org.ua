from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns(
    '',
    url(r'^select2/', include('select2.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
