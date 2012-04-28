from django.conf.urls import patterns, url
from piston.resource import Resource
import handlers

class CsrfExemptResource(Resource):
    def __init__(self, handler, authentication=None):
        super(CsrfExemptResource, self).__init__(handler, authentication)
        self.csrf_exempt = getattr(self.handler, 'csrf_exempt', True)

job_handler = CsrfExemptResource(handlers.JobHandler)

urlpatterns = patterns('',
    (r'^jobs/$', job_handler, {"spew_all": True}),
    (r'^result/(?P<job_id>\w{32})/$', job_handler),
    (r'^submit/', job_handler),
)