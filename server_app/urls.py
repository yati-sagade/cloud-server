from django.conf.urls import patterns, url
from documents import Job
from django.views.generic.simple import direct_to_template
import views


urlpatterns = patterns('',
        (r'^$', views.home),
        (r'^register/$', views.register),
        (r'^registered/$', views.registered),
        (r'^logout/$', views.logout_view),
        (r'^submit_job/$', views.submit_job),
        (r'^result/(?P<job_id>\w{32})/$', views.job_detail, {}, 'job_detail'),
        (r'^verify/$', views.verify),
        (r'^about/$', direct_to_template, {"template": "about.html"}),
)


