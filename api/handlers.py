from piston.handler import BaseHandler
from piston.utils import rc, throttle
from server_app.documents import Job, UserProfile
from server_app.forms import JobSubmitForm
from server_app.views import get_controller
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import redis
from mongoengine.base import ValidationError

redisClient = redis.StrictRedis()

class JobHandler(BaseHandler):
    allowed_methods = ('GET', 'POST')
    model = Job

    @classmethod
    def read(kls, request, job_id=None, spew_all=False):
        username, api_key = (request.GET.get("username", None), 
                             request.GET.get("api_key", None))
        if None in (username, api_key):
            return rc.BAD_REQUEST

        user = UserProfile.find(username)
        if user:
            if user.verified and user.api_key == api_key:
                if spew_all:
                    ret = map(Job.get_restricted, Job.objects.filter(owner=username))
                else:
                    if job_id:
                        ret = Job.objects.get(job_id=job_id).get_restricted()
                return HttpResponse(json.dumps(ret), content_type="application/json")
        return rc.FORBIDDEN

    @classmethod
    @throttle(3, 60)
    def create(kls, request):
        username, api_key = (request.POST.get("username", None), 
                             request.POST.get("api_key", None))
        if None in (username, api_key):
            return rc.BAD_REQUEST

        user = UserProfile.find(username)
        if user:
            if user.verified and user.api_key == api_key:
                form = JobSubmitForm(request.POST)
                if not form.is_valid():
                    return rc.BAD_REQUEST
                cd = form.cleaned_data
                func, args, ctx = (cd["func"], 
                                   json.loads(cd["args"]),
                                   json.loads(cd["ctx"]))

                job = {"func": func, "args": args, "ctx": ctx}
                c = get_controller()
              
                job_doc = Job.objects.create(job=job, 
                                             remaining=len(job["args"]),
                                             owner=username,
                                             assigned_to=c.get_name())
                
                redisClient.lpush(c.get_name(), 
                                  json.dumps(
                                    {"job_id": job_doc.job_id,
                                     "job": job}))

                return HttpResponse(json.dumps({"job_id": job_doc.job_id}), 
                                                content_type="application/json")
        return rc.FORBIDDEN