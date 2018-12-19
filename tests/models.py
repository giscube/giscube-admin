# -*-  coding: utf-8 -*-
from django.contrib.gis.db import models


class Location(models.Model):
    address = models.CharField(max_length=50, blank=True, null=True)
    geometry = models.PointField()
