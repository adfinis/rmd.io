from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^browserid/', include('django_browserid.urls')),
    url(r'^', include('mails.urls')),
)
