from django.db import models

# Create your models here.
class Documentation(models.Model):
    title = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    body = models.TextField()
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.title