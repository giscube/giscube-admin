# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
from django.forms import ModelForm, HiddenInput

from .models import DataBaseLayer


class DataBaseLayerAddForm(ModelForm):
    def clean(self):
        table = self.cleaned_data['table']
        geom_field = self.cleaned_data['geom_field']
        db_connection = self.cleaned_data['db_connection'].connection_name()
        GeometryColumns = self.cleaned_data[
            'db_connection'].get_connection().ops.geometry_columns()
        fields = GeometryColumns.objects.using(
            db_connection).all()
        has_geometry = False
        geom_field_has_geometry = False
        for f in fields:
            if table == getattr(f, f.table_name_col()):
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
