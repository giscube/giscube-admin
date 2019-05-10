from django import forms
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from giscube.models import DBConnection
from giscube.db.utils import get_table_parts

from .models import DataBaseLayer, DataBaseLayerField, GeoJsonLayer
from .model_legacy import get_fields
from .widgets import widgets_types


class DataBaseLayerFormMixin(object):
    def _clean_pk_field(self, db_connection, table):
        pk_field = self.cleaned_data.get('pk_field', None)
        if table is not None and pk_field is not None:
            table_parts = get_table_parts(table)
            table_schema = table_parts['table_schema']
            table = table_parts['fixed']

            # Check pk_field
            fields = get_fields(db_connection.get_connection(schema=table_schema), table)
            if self.cleaned_data['pk_field'] not in (None, '') and \
                    self.cleaned_data['pk_field'] not in list(fields.keys()):
                raise ValidationError('The field [%s] doesn\'t exist' % self.cleaned_data['pk_field'])

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
                    raise ValidationError('A primary key or AutoField is needed for pk_field')

        return self.cleaned_data['pk_field']


class DataBaseLayerAddForm(forms.ModelForm, DataBaseLayerFormMixin):
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

    def clean_table(self):
        table_parts = get_table_parts(self.cleaned_data['table'])
        table_name = table_parts['table_name']
        table_schema = table_parts['table_schema']
        table = table_parts['fixed']
        try:
            columns = self.cleaned_data['db_connection'].geometry_columns()
        except Exception:
            raise ValidationError('ERROR getting geometry columns')
        exist = False
        for column in columns:
            if table_name == column['f_table_name'] and (
                'f_table_schema' not in column or (column['f_table_schema'] == table_schema)
            ):
                exist = True
                break
        if not exist:
            msg = 'Table [%s] doesn\'t have a geometry column. Try setting the schema in table name.' % (
                self.cleaned_data['table'])
            raise ValidationError(msg)

        return table

    def clean_geom_field(self):
        table = self.cleaned_data.get('table', None)
        if table is not None:
            table_parts = get_table_parts(self.cleaned_data['table'])
            table_name = table_parts['table_name']
            table_schema = table_parts['table_schema']
            table = table_parts['fixed']
            self.cleaned_data['table'] = table
            # Check geometry column
            geom_field = self.cleaned_data['geom_field']
            try:
                columns = self.cleaned_data['db_connection'].geometry_columns()
            except Exception:
                raise ValidationError('ERROR getting geometry columns')

            has_geometry = False
            geom_field_has_geometry = False

            for column in columns:
                if table_name == column['f_table_name'] and (
                    'f_table_schema' not in column or (column['f_table_schema'] == table_schema)
                ):
                    has_geometry = True
                    geom_col_name = column['f_geometry_column']
                    if geom_field != '':
                        if geom_field == geom_col_name:
                            geom_field_has_geometry = True
                    else:
                        self.cleaned_data['geom_field'] = geom_col_name
                        self.cleaned_data['srid'] = column['srid']
                        geom_field_has_geometry = True
                    break
            if not has_geometry:
                if self.cleaned_data['table'] != 'geom_field':
                    msg = 'The column [%s] doesn\'t exists in [%s]' % (
                        self.cleaned_data['geom_field'], self.cleaned_data['table'])
                    if table_schema is None:
                        msg = '%s. Try setting the schema in table name.' % msg
                    raise ValidationError(msg)
                else:
                    raise ValidationError(
                        'There isn\'t a geometry column in [%s]' % self.cleaned_data['table'])
            if not geom_field_has_geometry:
                raise ValidationError(
                    '[%s] is not geometry type or not exists' % self.cleaned_data['geom_field'])

        return self.cleaned_data['geom_field']

    def clean_pk_field(self):
        table = self.cleaned_data.get('table', None)
        pk_field = self.cleaned_data.get('pk_field', None)
        if table is not None and pk_field is not None:
            return self._clean_pk_field(self.cleaned_data['db_connection'], table)

    class Meta:
        model = DataBaseLayer
        exclude = ()
        fields = ('db_connection', 'geometry_columns', 'name', 'table', 'geom_field', 'srid', 'pk_field')


class DataBaseLayerChangeForm(forms.ModelForm, DataBaseLayerFormMixin):
    def clean_pk_field(self):
        pk_field = self.cleaned_data.get('pk_field', None)
        if pk_field is not None:
            return self._clean_pk_field(self.instance.db_connection, self.instance.table)

    class Meta:
        model = DataBaseLayer
        exclude = ()


class DataBaseLayerFieldsInlineForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        err = widgets_types[cleaned_data['widget']].is_valid(cleaned_data['widget_options'])
        if err is not None:
            self.add_error('widget_options', err)

    class Meta:
        model = DataBaseLayerField
        fields = '__all__'


class GeoJsonLayerAddForm(forms.ModelForm):
    class Meta:
        model = GeoJsonLayer
        exclude = ()


class GeoJsonLayerChangeForm(forms.ModelForm):
    force_refresh_data_file = forms.BooleanField(
        label=_('Force refresh Data file'), widget=forms.CheckboxInput, required=False, initial=False)

    class Meta:
        model = GeoJsonLayer
        exclude = ()
