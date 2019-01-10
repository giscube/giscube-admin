# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
from django.forms import ModelForm, HiddenInput

from .models import DataBaseLayer
from giscube.db.utils import get_table_parts


class DataBaseLayerAddForm(ModelForm):
    def clean(self):
        table_parts = get_table_parts(self.cleaned_data['table'])
        table_name = table_parts['table_name']
        table_schema = table_parts['table_schema']
        table = table_parts['fixed']
        # Fixed name
        self.cleaned_data['table'] = table

        geom_field = self.cleaned_data['geom_field']
        db_connection = self.cleaned_data['db_connection'].connection_name()
        GeometryColumns = self.cleaned_data[
            'db_connection'].get_connection().ops.geometry_columns()
        fields = GeometryColumns.objects.using(
            db_connection).all()
        has_geometry = False
        geom_field_has_geometry = False
        for f in fields:
            if table_name == getattr(f, f.table_name_col()) and (
                not hasattr(f, 'f_table_schema') or (getattr(f, 'f_table_schema') == table_schema)
            ):
                has_geometry = True
                geom_col_name = getattr(f, f.geom_col_name())
                if geom_field != '':
                    if geom_field == geom_col_name:
                        geom_field_has_geometry = True
                else:
                    self.cleaned_data['geom_field'] = geom_col_name
                    self.cleaned_data['srid'] = f.srid
                    geom_field_has_geometry = True
                break
        if not has_geometry:
            raise ValidationError(
                'There isn\'t a geometry column in %s' % table)
        if not geom_field_has_geometry:
            raise ValidationError(
                '%s is not geometry type' % self.cleaned_data['geom_field'])
        return self.cleaned_data

    class Meta:
        model = DataBaseLayer
        exclude = ()
        widgets = {'srid': HiddenInput()}


class DataBaseLayerChangeForm(ModelForm):
    class Meta:
        model = DataBaseLayer
        exclude = ()
