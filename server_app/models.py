from django.db import models

class Controller(models.Model):
    addr = models.CharField(max_length=100)
    port = models.IntegerField()
    state = models.IntegerField()
    
    def get_name(self):
        return self.addr + ':' + str(self.port)

    def __unicode__(self):
        return self.get_name()

