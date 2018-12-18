# -*-  coding: utf-8 -*-
from django.contrib.gis.db import models


class Location(models.Model):
    code = models.CharField(max_length=10, blank=False, null=False, unique=True)
    address = models.CharField(max_length=50, blank=True, null=True)
    geometry = models.PointField()
