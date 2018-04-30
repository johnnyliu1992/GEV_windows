from django.conf.urls import url
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns=[
			url(r'^$', views.index, name='index'),
			#url(r'^result$', views.result, name='result'),
			url(r'^analyze$', views.analyze, name='analyze'),
			#url(r'^download/(?P<file_name>.+)$', views.download,name='download'),
			url(r'^download_sample/(?P<file_name>.+)$', views.download_sample,name='download_sample'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)