import ujson as json

from django.contrib.gis.db import models
from django.contrib.gis.db.models.functions import Distance, GeoFunc, PointOnSurface
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVectorField
from django.db.models import Case, F, Q, When

from giscube import settings as custom_settings

from .utils import remove_accents


class ContainsFunc(GeoFunc):
    function = 'ST_contains'
    output_field = models.BooleanField()
    arity = 2


class DocumentIndexBaseQuerySet(models.QuerySet):
    def content_type(self, ct):
        return self.filter(content_type__in=ct)

    def geo_distance(self, latlon, radius):
        geom = Point(latlon[1], latlon[0])
        point_filter = Q(geom_point__isnull=False) & Q(geom_point__distance_lte=(geom, D(m=radius)))
        line_filter = Q(geom_linestring__isnull=False) & Q(geom_linestring__distance_lte=(geom, D(m=radius)))
        polygon_filter = Q(
            geom_polygon__isnull=False) & Q(geom_polygon__bbcontains=geom) & Q(geom_polygon__contains=geom)
        return self.filter(Q(point_filter) | Q(line_filter) | Q(polygon_filter)).annotate(
            distance=Distance(geom,
                              Case(
                                  When(geom_linestring__isnull=True, geom_polygon__isnull=True,
                                       then='geom_point'),
                                  When(geom_point__isnull=True, geom_polygon__isnull=True,
                                       then=PointOnSurface('geom_linestring')),
                                  When(geom_point__isnull=True, geom_linestring__isnull=True,
                                       then=PointOnSurface('geom_polygon'))
                              )
                              )
        ).order_by('distance')

    def geo_intersects(self, geom):
        point_filter = Q(geom_point__isnull=False) & Q(geom_point__intersects=geom)
        line_filter = Q(geom_linestring__isnull=False) & Q(geom_linestring__intersects=geom)
        polygon_filter = Q(geom_polygon__isnull=False) & Q(geom_polygon__intersects=geom)
        return self.filter(Q(point_filter) | Q(line_filter) | Q(polygon_filter)).annotate(
            distance=Distance(geom,
                              Case(
                                  When(geom_linestring__isnull=True, geom_polygon__isnull=True,
                                       then='geom_point'),
                                  When(geom_point__isnull=True, geom_polygon__isnull=True,
                                       then=PointOnSurface('geom_linestring')),
                                  When(geom_point__isnull=True, geom_linestring__isnull=True,
                                       then=PointOnSurface('geom_polygon'))
                              )
                              )
        ).order_by('distance')

    def geo_contains(self, geom):
        return self.filter(
            Q(geom_polygon__isnull=False)
        ).annotate(
            is_contained=ContainsFunc(geom, F('geom_polygon'))
        ).filter(
            is_contained=True
        ).annotate(
            distance=Distance(geom, PointOnSurface('geom_polygon'))
        ).order_by('distance')

    def search(self, q):
        q = remove_accents(q)
        query = SearchQuery(q, config=custom_settings.GISCUBE_SEARCH_DEFAULT_DICTIONARY)
        return self.annotate(rank=SearchRank(F('body'), query)).filter(body=query).order_by('-rank')


class DocumentIndexBaseManager(models.Manager):
    def get_queryset(self):
        return DocumentIndexBaseQuerySet(self.model, using=self._db).filter(indexing=False)

    def content_type(self, ct):
        qs = self.get_queryset()
        return qs.content_type(ct)

    def geo(self, latlon, radius):
        qs = self.get_queryset()
        return qs.geo(latlon)

    def search(self, q):
        return self.get_queryset().search(q)


class BaseDocumentIndex(models.Model):
    content_type = models.CharField(max_length=255, db_index=True)
    object_id = models.CharField(max_length=255)
    body = SearchVectorField()
    output_data = models.JSONField(null=True, blank=True)
    search_data = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    geom_point = models.MultiPointField(null=True, blank=True)
    geom_linestring = models.MultiLineStringField(null=True, blank=True)
    geom_polygon = models.MultiPolygonField(null=True, blank=True)
    indexing = models.BooleanField(default=False, db_index=True)

    objects = DocumentIndexBaseManager()
    objects_default = models.Manager()

    def get_geom(self, srid):
        value = self.geom_point or self.geom_linestring or self.geom_polygon
        if value:
            value.transform(srid)
            return json.loads(value.json)

    class Meta:
        abstract = True
        unique_together = ('content_type', 'object_id')
        index_together = [['content_type', 'indexing']]
        indexes = [GinIndex(fields=['body'])]

    def __str__(self):
        return '%s: %s' % (self.content_type, self.object_id)
