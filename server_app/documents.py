import mongoengine
from mongoengine.django import auth
from django.db.models import permalink
import uuid
import datetime
try:
    import json
except ImportError:
    from django.utils import simplejson as json

class UserProfile(auth.User):
    verified = mongoengine.BooleanField()
    api_key = mongoengine.StringField()
    verify_hash = mongoengine.StringField()
    
    @classmethod
    def find(kls, email):
        try:
            user = kls.objects.get(username=email)
        except kls.DoesNotExist:
            user = None
        return user

class Job(mongoengine.Document):
    job_id = mongoengine.StringField(default=lambda: uuid.uuid4().hex)
    job = mongoengine.DictField()
    status = mongoengine.IntField(default=0)
    owner = mongoengine.EmailField()
    submitted_at = mongoengine.DateTimeField(default=datetime.datetime.now)
    finished_at = mongoengine.DateTimeField()
    result = mongoengine.DictField(default=dict)
    assigned_to = mongoengine.StringField()
    remaining = mongoengine.IntField()

    def get_owner(self):
        return UserProfile.objects.get(username=self.owner)

    @permalink
    def get_absolute_url(self):
        return 'job_detail', (), {"job_id": self.job_id}

    @staticmethod
    def _get_status_by_status_id(id):
        m = ('queued', 'processing', 'done',)
        return m[id]

    def __unicode__(self):
        return self.job_id

    def get_restricted(self):
        return {
            "job_id": self.job_id,
            "job": self.job,
            "status": self._get_status_by_status_id(self.status),
            "submitted_at": str(self.submitted_at),
            "result": self.result
        }



