# -*-  coding: utf-8 -*-
from django.contrib.gis.db import models


class Location(models.Model):
    code = models.CharField(max_length=10, blank=False, null=False, unique=True)
    address = models.CharField(max_length=50, blank=True, null=True)
    geometry = models.PointField()


class TestField(models.Model):
    code = models.CharField(max_length=10, blank=False, null=False, unique=True)
    name = models.CharField(max_length=50, blank=True, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    x = models.FloatField(blank=True, null=True)
    y = models.FloatField(blank=True, null=True)
    geometry = models.PointField()
