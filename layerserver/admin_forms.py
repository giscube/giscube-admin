import json

from django import forms
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils.translation import gettext as _

from giscube.db.utils import get_table_parts
from giscube.models import DBConnection
from giscube.widgets import ColorWidget, TagsWidget

from .model_legacy import get_fields
from .models import (DataBaseLayer, DataBaseLayerField, DataBaseLayerReference, DataBaseLayerStyleRule,
                     DataBaseLayerVirtualField, GeoJsonLayer, GeoJsonLayerStyleRule)
from .widgets import widgets_types


class ClusterFormMixin(forms.ModelForm):
    def clean_cluster_options(self):
        if self.cleaned_data['cluster_options'] is not None and self.cleaned_data['cluster_options'] != '':
            try:
                data = json.loads(self.cleaned_data['cluster_options'])
            except Exception:
                raise forms.ValidationError(_('Invalid JSON format'))
            return json.dumps(data, indent=4)


class DataBaseLayerFormMixin(ClusterFormMixin, forms.ModelForm):
    def validate_pk_field(self, db_connection, table_name):
        table_parts = get_table_parts(table_name)
        table_schema = table_parts['table_schema']

        # Check pk_field
        fields = get_fields(db_connection.get_connection(schema=table_schema), table_name)
        if self.cleaned_data['pk_field'] not in (None, '') and \
                self.cleaned_data['pk_field'] not in list(fields.keys()):
            return 'The field [%s] doesn\'t exist' % self.cleaned_data['pk_field']

        # Look for a primary_key or AutoField
        if self.cleaned_data['pk_field'] in (None, ''):
            primary_key = None
            for field_name, field in list(fields.items()):
                if getattr(field, 'primary_key'):
                    primary_key = field_name
                    break
            if primary_key:
                self.cleaned_data['pk_field'] = primary_key
            else:
                auto_field = None
                for field_name, field in list(fields.items()):
                    if isinstance(field, models.AutoField):
                        auto_field = field_name
                        break
                if auto_field:
                    self.cleaned_data['pk_field'] = auto_field

            if primary_key is None and auto_field is None:
                return 'A primary key or AutoField is needed for pk_field'

    def clean_name(self):
        return slugify(self.cleaned_data['name'])


class DataBaseLayerAddForm(DataBaseLayerFormMixin, forms.ModelForm):
    geometry_columns = forms.ChoiceField(choices=(), widget=forms.Select(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        table_choices = [('', '--')]
        db_connection = None
        if 'db_connection' in self.data and self.data['db_connection'] is not None:
            try:
                db_connection = DBConnection.objects.get(pk=self.data['db_connection'])
            except Exception:
                pass
        if db_connection is not None:
            columns = db_connection.geometry_columns()
            for i, column in enumerate(columns):
                table_choices.append((i, column['label']))
        self.fields['geometry_columns'].choices = table_choices

    def is_valid_geom_field(self):
        table = self.cleaned_data.get('table', None)
        if table is not None and 'geom_field' in self.cleaned_data and self.cleaned_data['geom_field'] is not None:
            table_parts = get_table_parts(table)
            table_name = table_parts['table_name']
            table_schema = table_parts['table_schema']
            table = table_parts['fixed']
            self.cleaned_data['table'] = table

            geom_field = self.cleaned_data['geom_field']
            try:
                columns = self.cleaned_data['db_connection'].geometry_columns()
            except Exception:
                raise Exception(_('ERROR getting geometry columns'))

            has_geometry = False
            for column in columns:
                if table_name == column['f_table_name'] and (
                    'f_table_schema' not in column or (column['f_table_schema'] == table_schema)
                ):
                    geom_col_name = column['f_geometry_column']
                    if geom_field == '':
                        self.cleaned_data['geom_field'] = geom_col_name
                        has_geometry = True
                        break
                    else:
                        if geom_field == geom_col_name:
                            has_geometry = True
                            break
            return has_geometry

    def is_valid_table(self, table):
        db_connection = self.cleaned_data['db_connection']
        return db_connection.table_exists(table)

    def clean(self):
        super().clean()
        table = self.cleaned_data['table']
        if not self.is_valid_table(table):
            self.add_error('table', _('Table [%s] doesn\'t exist') % table)
            return

        if self.cleaned_data['geom_field'] is not None and self.cleaned_data['geom_field'] != '':
            if not self.is_valid_geom_field():
                msg = _('[%s] is not geometry type or not exists') % self.cleaned_data['geom_field']
                self.add_error('geom_field', msg)
                return

        db_connection = self.cleaned_data.get('db_connection')
        err = self.validate_pk_field(db_connection, table)
        if err is not None:
            self.add_error('pk_field', err)

    def clean_table(self):
        table_parts = get_table_parts(self.cleaned_data['table'])
        return table_parts['fixed']

    def clean_srid(self):
        geom_field = self.cleaned_data.get('geom_field', None)
        srid = self.cleaned_data.get('srid', None)
        if geom_field is not None and srid is None:
            raise ValidationError(_('Srid is required'))
        return srid

    class Meta:
        model = DataBaseLayer
        exclude = ()
        fields = ('db_connection', 'geometry_columns', 'name', 'table', 'geom_field', 'srid', 'pk_field')


class DataBaseLayerChangeForm(DataBaseLayerFormMixin, forms.ModelForm):
    def _split_comma(self, value):
        return list(filter(None, [x.strip() for x in value.split(',')]))

    def clean_form_fields(self):
        values = self._split_comma(self.cleaned_data.get('form_fields', ''))
        return ','.join(values)

    def clean_list_fields(self):
        values = self._split_comma(self.cleaned_data.get('list_fields', ''))
        return ','.join(values)

    def clean(self):
        cleaned_data = super().clean()
        err = self.validate_pk_field(self.instance.db_connection, self.instance.table)
        if err is not None:
            self.add_error('pk_field', err)
            return

        form_fields = self._split_comma(cleaned_data.get('form_fields', ''))
        list_fields = self._split_comma(cleaned_data.get('list_fields', ''))

        fields_count = int(self.data.get('fields-TOTAL_FORMS', 0))
        fields_enabled = []
        virtual_enabled = []
        for i in range(0, fields_count):
            if self.data.get('fields-{0}-enabled'.format(i), '') == 'on':
                fields_enabled.append(i)
            if self.data.get('virtual_fields-{0}-enabled'.format(i), '') == 'on':
                virtual_enabled.append(self.data.get('virtual_fields-{0}-name'.format(i)))
        enabled_names = [] + virtual_enabled
        for i, x in enumerate(self.instance.fields.all()):
            if i in fields_enabled:
                enabled_names.append(x.name)

        list_fields_errors = []
        for x in list_fields:
            if x not in enabled_names:
                list_fields_errors.append(x)
        if len(list_fields_errors) > 0:
            self.add_error('list_fields', _('[%s] doesn\'t exist or aren\'t enabled.') %
                           ', '.join(list_fields_errors))
            return

        form_fields_errors = []
        for x in form_fields:
            if x not in enabled_names:
                form_fields_errors.append(x)
        if len(form_fields_errors) > 0:
            self.add_error('form_fields', _('[%s] doesn\'t exist or aren\'t enabled.') %
                           ', '.join(form_fields_errors))
            return

    class Meta:
        model = DataBaseLayer
        exclude = ()
        widgets = {
            'stroke_color': ColorWidget,
            'fill_color': ColorWidget,
            'marker_color': ColorWidget,
            'icon_color': ColorWidget,
            'form_fields': TagsWidget,
            'list_fields': TagsWidget
        }


class DataBaseLayerFieldsInlineForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        err = widgets_types[cleaned_data['widget']].is_valid(cleaned_data)
        if err is not None:
            self.add_error('widget_options', err)

    class Meta:
        model = DataBaseLayerField
        fields = '__all__'


class DataBaseLayerReferencesInlineForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        jpeg = getattr(DataBaseLayerReference.IMAGE_FORMAT_CHOICES, 'image/jpeg')
        if 'format' in cleaned_data and 'transparent' in cleaned_data and (
                cleaned_data['format'] == jpeg and cleaned_data['transparent'] is True):
            error = _('%s format doesn\'t support transparent attribute enabled') % \
                DataBaseLayerReference.IMAGE_FORMAT_CHOICES['image/jpeg']
            self.add_error('transparent', error)

    class Meta:
        model = DataBaseLayerReference
        exclude = []


class DataBaseLayerStyleRuleInlineForm(forms.ModelForm):
    class Meta:
        model = DataBaseLayerStyleRule
        fields = '__all__'
        widgets = {
            'stroke_color': ColorWidget,
            'fill_color': ColorWidget,
            'marker_color': ColorWidget,
            'icon_color': ColorWidget,
        }


class DataBaseLayerVirtualFieldsInlineForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        if 'widget' in cleaned_data and cleaned_data['widget'] in widgets_types:
            err = widgets_types[cleaned_data['widget']].is_valid(cleaned_data)
            if err is not None:
                self.add_error('widget_options', err)

    class Meta:
        model = DataBaseLayerVirtualField
        fields = '__all__'


class GeoJsonLayerAddForm(ClusterFormMixin, forms.ModelForm):
    # Fake save_as_new
    force_refresh_data_file = forms.BooleanField(label=_('Force refresh Data file'), required=False, initial=True)
    generate_popup = forms.BooleanField(label=_('Generate popup from data'), required=False, initial=False)

    def clean_name(self):
        return slugify(self.cleaned_data['name'])

    class Meta:
        model = GeoJsonLayer
        exclude = ()
        widgets = {
            'stroke_color': ColorWidget,
            'fill_color': ColorWidget,
            'marker_color': ColorWidget,
            'icon_color': ColorWidget
        }


class GeoJsonLayerChangeForm(ClusterFormMixin, forms.ModelForm):
    force_refresh_data_file = forms.BooleanField(label=_('Force refresh Data file'), required=False, initial=False)
    generate_popup = forms.BooleanField(label=_('Generate popup from data'), required=False, initial=False)

    def clean_name(self):
        return slugify(self.cleaned_data['name'])

    class Meta:
        model = GeoJsonLayer
        exclude = ()
        widgets = {
            'stroke_color': ColorWidget,
            'fill_color': ColorWidget,
            'marker_color': ColorWidget,
            'icon_color': ColorWidget,
        }


class GeoJsonLayerStyleRuleInlineForm(forms.ModelForm):
    class Meta:
        model = GeoJsonLayerStyleRule
        fields = '__all__'
        widgets = {
            'stroke_color': ColorWidget,
            'fill_color': ColorWidget,
            'marker_color': ColorWidget,
            'icon_color': ColorWidget,
        }
