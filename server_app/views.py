from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from documents import UserProfile, Job

def home(request):
    if request.user.is_authenticated():
        user = UserProfile.objects.get(username=request.user.username)
        jobs = Job.objects.filter(owner=user.username)

        return render_to_response("home.html", 
                                   {"user": user, "jobs": jobs},
                                   RequestContext(request))

    return render_to_response("login.html", RequestContext(request))


@login_required(login_url='/')
def job_detail(request, job_id):
    job = get_object_or_404(Job, job_id=job_id)
    return render_to_response("job_detail.html", {"job": job})

@login_required(login_url="/")
def submit_job(request):
    if request.method == 'POST':
        