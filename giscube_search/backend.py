import logging
import traceback

from django.contrib.gis.geos import MultiLineString, MultiPoint, MultiPolygon
from django.contrib.postgres.search import SearchVector
from django.db import transaction
from django.db.models import TextField, Value
from django.forms.models import model_to_dict
from django.utils.encoding import force_str

from giscube import settings as custom_settings

from .base_index import BaseGeomIndexMixin
from .model_utils import DocumentIndexEditor


logger = logging.getLogger(__name__)


class PostgresSearchIndex:
    MULTI_GEOM_CLASSES = {
        'MULTILINESTRING': MultiLineString,
        'MULTIPOINT': MultiPoint,
        'MULTIPOLYGON': MultiPolygon
    }

    def __init__(self, config):
        self.config = config
        self.language = self.config.get_context().get('language', custom_settings.GISCUBE_SEARCH_DEFAULT_DICTIONARY)
        logger.info('Indexing [%s]' % self.config.get_content_type())

    def get_obj_pk(self, obj):
        return force_str(self.config.prepare_object_id(obj))

    def add_items(self, objs=None):
        DocumentIndexEditorModel = DocumentIndexEditor(name=self.config.get_index()).get_model()
        content_type = self.config.get_content_type()
        filter = {'indexing': True, 'content_type': content_type}
        if objs is not None:
            pks = [self.get_obj_pk(obj) for obj in objs]
            filter['object_id__in'] = pks
        else:
            objs = self.config.get_items()

        documents = DocumentIndexEditorModel.objects_default.filter(**filter)
        documents._raw_delete(documents.db)

        is_geom = isinstance(self.config, BaseGeomIndexMixin)
        for obj in objs:
            try:
                body = ' '.join(self.config.prepare_body(obj))
                attrs = {
                    'content_type': content_type,
                    'object_id': self.get_obj_pk(obj),
                    'body': SearchVector(Value(body, output_field=TextField()), config=self.language),
                    'output_data': self.config.prepare_output_data(obj),
                    'search_data': self.config.prepare_search_data(obj),
                    'metadata': self.config.prepare_metadata(obj)
                }
            except Exception as e:
                logger.error('ERROR indexing [%s]' % self.config.get_content_type())
                logger.error(traceback.format_exc())
                logger.debug(str(e))
                logger.debug(model_to_dict(obj))
                continue

            metadata = self.config.prepare_metadata(obj)
            if is_geom:
                geom = self.config.prepare_geom_field(obj)
                if geom:
                    if metadata.get('srid', '4326') != 4326:
                        geom.transform(4326)
                    if not metadata.get('geom_type').startswith('MULTI'):
                        geom_class = self.MULTI_GEOM_CLASSES['MULTI%s' % metadata.get('geom_type')]
                        geom = geom_class(geom)
                geom_index_field = 'geom_%s' % metadata.get('geom_type').replace('MULTI', '').lower()
                attrs[geom_index_field] = geom
            attrs['indexing'] = True
            DocumentIndexEditorModel.objects_default.create(**attrs)

        with transaction.atomic():
            filter['indexing'] = False
            documents = DocumentIndexEditorModel.objects_default.filter(**filter)
            documents._raw_delete(documents.db)
            filter['indexing'] = True
            DocumentIndexEditorModel.objects_default.filter(**filter).update(indexing=False)
