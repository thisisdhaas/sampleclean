from django.conf.urls import patterns, url

from amt import views

urlpatterns = patterns('',
                       url(r'^tasks/(?P<task_id>\d+)/$', views.display_task, name='display_task'),
)
