import mongoengine
from mongoengine.django import auth
import uuid

class Job(mongoengine.Document):
    job_id = mongoengine.StringField(primary_key=True, default=uuid.uuid4.hex)
    job = mongoengine.DictField()
    status = mongoengine.IntField()
    owner = mongoengine.EmailField()
    submitted_at = mongoengine.DateTimeField()
    finished_at = mongoengine.DateTimeField()
    result = mongoengine.DictField()
    assigned_to = mongoengine.StringField()
    remaining = mongoengine.IntField()

    def get_owner(self):
        return auth.User.objects.get(username=self.owner)

    def get_absolute_url(self):

    def __unicode__(self):
        return self.job_id

class UserProfile(auth.User):
    verified = mongoengine.BooleanField()
    api_key = mongoengine.StringField()