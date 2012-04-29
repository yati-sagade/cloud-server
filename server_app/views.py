from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from documents import UserProfile, Job
from forms import RegistrationForm, LoginForm, JobSubmitForm
from django.http import HttpResponse, Http404
from django.contrib.auth import login, logout
from django.core.mail import EmailMessage
from django.template import Context
from models import Controller
from django.conf import settings
import redis
import datetime
import urllib
import uuid
import os

try:
    import json
except ImportError:
    from django.utils import simplejson as json

redisClient = redis.StrictRedis()

def _random_MD5():
    return ''.join('%02x' % ord(x) for x in os.urandom(16))

def home(request):
    if request.user.is_authenticated():
        user = UserProfile.objects.get(username=request.user.username)
        jobs = Job.objects.filter(owner=user.username)

        return render_to_response("home.html", 
                                 {"user": user, "jobs": jobs, "job_form": JobSubmitForm()},
                                   RequestContext(request))
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            email, password = cd['email'], cd['password']
            user = UserProfile.find(email)
            if user:
                if user.check_password(password):
                    user.backend = 'mongoengine.django.auth.MongoEngineBackend'
                    login(request, user)
                    if request.GET.get('next', None):
                        return redirect(request.GET['next'])
                    return redirect('/')
            return HttpResponse("invalid login")
        return redirect('/') 
    return render_to_response("login.html", 
                              {"login_form": LoginForm(),
                               "registration_form": RegistrationForm()},
                                RequestContext(request))

def register(request):
    if request.method == 'POST' and not request.user.is_authenticated():
        form = RegistrationForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            username, password, name = cd['email'], cd['password'], cd['name']
            try:
                UserProfile.objects.get(username=username)
                return redirect('/already_registered/')
            except:
                verify_hash = _random_MD5()
                u = UserProfile.objects.create(username=username,
                                               email=username,
                                               first_name=name,
                                               verified=False,
                                               verify_hash=verify_hash)
            u.set_password(password)
            msgstr = settings.VERIFICATION_MAIL_BODY_TEMPLATE.render(
                Context({
                    "username": name, 
                    "verification_link": 
                          request.build_absolute_uri('/')
                        + 'verify/?'
                        + urllib.urlencode((
                            ("username", username),
                            ("verify", verify_hash),
                        ))
                })
            )
            EmailMessage('Welcome to cloud.js', msgstr, to=[username]).send()
            return redirect("/registered/")
        
        return HttpResponse("Form invalid")
    return HttpResponse("hmmmm " + request.method + " " + str(request.user.is_authenticated()))

def registered(request):
    return render_to_response("message.html",
                    {"message": 
                    "A mail has been sent to your email with the next steps."})

def verify(request):
    username, verify_hash = (request.GET.get("username", None),
                             request.GET.get("verify", None))
    u = UserProfile.find(username)
    if not u:
        msg = "Sorry, that email &mdash; {0} &mdash; is not in our database.".format(username)
    else:
        if u.verified:
            msg = "We believe that this email &mdash; {0} &mdash; is already activated."
        else:
            if u.verify_hash == verify_hash:
                u.verified = True
                u.api_key = uuid.uuid4().hex
                u.save()
                body = settings.POST_VERIFICATION_MAIL_BODY_TEMPLATE.render(
                    Context({
                        "api_key": u.api_key
                    })
                )
                EmailMessage('cloud.js API key', body, to=[username]).send()
                msg = ('A mail with the API key has been sent to your email'
                    + ' account. You can also <a href="/">login</a> and submit'
                    + ' jobs from the web interface now.')
            else:
                msg = 'Sorry, invalid attempt.'
    return render_to_response("message.html", {"message": msg})

@login_required(login_url='/')
def job_detail(request, job_id):
    try:
        job_doc = Job.objects.get(job_id=job_id)
    except Job.DoesNotExist:
        raise Http404

    arg_result_ctx = []
    for i in xrange(len(job_doc.job["args"])):
        arg = job_doc.job["args"][i]
        resultDict = job_doc.result.get(str(i), None)
        if resultDict:
            if not resultDict.get("error", None):
                ctx = resultDict.get("ctx", None)
                ret = resultDict.get("ret", None)
            else:
                ret, ctx = resultDict["error"], None
        else:
            ctx, ret = None, None
        arg_result_ctx.append((arg, ret, ctx))

    return render_to_response("job_detail.html", 
                                 {"job": job_doc,
                                  "arc": arg_result_ctx
                                 })

def get_controller():
    # Simple LRU
    controllers = Controller.objects.filter(state=0).order_by('timestamp')
    the_one = None
    for c in controllers:
        try:
            fp = urllib.urlopen('http://' + c.get_name() + '/ping/')
            print('pinging %s' % c.get_name())
            resp = fp.read()
            print('read: %s' % resp)
            if resp.strip() == '"pong"':
                c.save()
                return c
            c.state = 1
            c.save()
        except IOError:
            c.state = 1
            c.save()

    return None

@login_required(login_url="/")
def submit_job(request):
    if request.method == 'POST':
        form = JobSubmitForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            func, args, ctx = cd['func'], json.loads(cd['args']), json.loads(cd['ctx'])
            job = {"func": func, "args": args, "ctx": ctx}
            c = get_controller()
            print(str(c) + ' selected now.') 
            job_doc = Job.objects.create(job=job, 
                                         remaining=len(job["args"]),
                                         owner=request.user.username,
                                         assigned_to=c.get_name())
            redisClient.lpush(c.get_name(), json.dumps({"job_id": job_doc.job_id, "job": job}))
            return redirect('/')
        request.session['error'] = 'Form improperly filled'
    return redirect('/')



@login_required(login_url="/")
def logout_view(request):
    logout(request)
    return redirect('/')

