from django.contrib.auth.models import User
from django.contrib.gis.db import models


class Incidence(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    geometry = models.GeometryField()
