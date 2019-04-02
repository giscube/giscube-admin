# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
from django.forms import ModelForm

from giscube.models import DBConnection
from giscube.db.utils import get_table_parts

from .models import DataBaseLayer
from .model_legacy import get_fields


from django import forms


class DataBaseLayerAddForm(ModelForm):
    geometry_columns = forms.ChoiceField(choices=(), widget=forms.Select(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        table_choices = [('', '--')]
        db_connection = None
        if 'db_connection' in self.data and len(self.data['db_connection']) == 1:
            db_connection = DBConnection.objects.get(pk=self.data['db_connection'][0])
        if db_connection is not None:
            columns = db_connection.geometry_columns()
            for i, column in enumerate(columns):
                table_choices.append((i, column['label']))
        self.fields['geometry_columns'].choices = table_choices

    def clean(self):
        super().clean()
        table_parts = get_table_parts(self.cleaned_data['table'])
        table_name = table_parts['table_name']
        table_schema = table_parts['table_schema']
        table = table_parts['fixed']
        # Fixed name
        self.cleaned_data['table'] = table
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
                raise ValidationError(
                    'The column [%s] doesn\'t exists in [%s]' % (
                        self.cleaned_data['geom_field'], self.cleaned_data['table']))
            else:
                raise ValidationError(
                    'There isn\'t a geometry column in [%s]' % self.cleaned_data['table'])
        if not geom_field_has_geometry:
            raise ValidationError(
                '%s is not geometry type' % self.cleaned_data['geom_field'])
        return self.cleaned_data

    class Meta:
        model = DataBaseLayer
        exclude = ()
        fields = ('db_connection', 'geometry_columns', 'slug', 'name', 'table', 'geom_field', 'srid')


class DataBaseLayerChangeForm(ModelForm):
    def clean(self):
        table_parts = get_table_parts(self.instance.table)
        table_schema = table_parts['table_schema']
        table = table_parts['fixed']

        fields = get_fields(self.cleaned_data['db_connection'].get_connection(schema=table_schema), table)
        pk_field_exists = False
        for f in fields:
            if f == self.cleaned_data['pk_field']:
                pk_field_exists = True
                break
        if not pk_field_exists:
            raise ValidationError('The Pk field [%s] doesn\'t exist' % self.cleaned_data['pk_field'])
        return self.cleaned_data

    class Meta:
        model = DataBaseLayer
        exclude = ()
