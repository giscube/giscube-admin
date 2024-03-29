# -*-  coding: utf-8 -*-
from django.contrib.gis.db import models


class Location(models.Model):
    code = models.CharField(max_length=10, blank=False, null=False, unique=True)
    address = models.CharField(max_length=50, blank=True, null=True)
    geometry = models.PointField()


class LocationNullGeometry(models.Model):
    code = models.CharField(max_length=10, blank=False, null=False, unique=True)
    address = models.CharField(max_length=50, blank=True, null=True)
    geometry = models.PointField(blank=True, null=True)


class LocationAuto(models.Model):
    code = models.CharField(max_length=10, blank=False, null=False, unique=True)
    address = models.CharField(max_length=50, blank=True, null=True)
    creationuser = models.CharField(max_length=50, blank=True, null=True)
    modificationuser = models.CharField(max_length=50, blank=True, null=True)
    creationdate = models.DateField(blank=True, null=True)
    modificationdate = models.DateField(blank=True, null=True)
    creationdatetime = models.DateTimeField(blank=True, null=True)
    modificationdatetime = models.DateTimeField(blank=True, null=True)
    geometry = models.PointField()


class Location_25831(models.Model):
    code = models.CharField(max_length=10, blank=False, null=False, unique=True)
    address = models.CharField(max_length=50, blank=True, null=True)
    geometry = models.PointField(srid=25831)


class TestField(models.Model):
    code = models.CharField(max_length=10, blank=False, null=False, unique=True)
    name = models.CharField(max_length=50, blank=True, null=True)
    enabled = models.BooleanField()
    accepted = models.BooleanField(null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    x = models.FloatField(blank=True, null=True)
    y = models.FloatField(blank=True, null=True)
    geometry = models.PointField()


class TestImageField(models.Model):
    code = models.CharField(max_length=10, blank=False, null=False, unique=True)
    image = models.CharField(max_length=255, blank=True, null=True)
    geometry = models.PointField()


class Specie(models.Model):
    code = models.CharField(max_length=25, blank=False, null=False, unique=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    image = models.CharField(max_length=255, blank=True, null=True)
