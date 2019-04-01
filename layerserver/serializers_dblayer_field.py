from rest_framework import serializers

from layerserver.models import DataBaseLayerField


class DBLayerFieldListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        data = data.filter(enabled=True)
        return super(
            DBLayerFieldListSerializer, self).to_representation(data)


class DBLayerFieldSerializer(serializers.ModelSerializer):
    def _serialize_auto(self, obj, data):
        data['widget'] = obj.field_type

    def _serialize_choices(self, obj, data):
        rows = []
        if obj.widget_options is not None:
            for line in obj.widget_options.splitlines():
                parts = line.split(',')
                if len(parts) == 1:
                    rows.append(parts[0])
                elif len(parts) == 2:
                    rows.append(parts)
                else:
                    rows.append('error')
        data['values_list'] = rows

    def _serialize_linkedfield(self, obj, data):
        data['widget_options'] = obj.widget_options

    def _serialize_sqlchoices(self, obj, data):
        headers = []
        rows = []
        if obj.widget_options is not None:
            with obj.layer.db_connection.get_connection().cursor() as cursor:
                cursor.execute('%s LIMIT 0' % obj.widget_options)
                for header in cursor.description:
                    headers.append(header.name)
                cursor.execute(obj.widget_options)
                for r in cursor.fetchall():
                    if len(r) == 1:
                        rows.append(r[0])
                    else:
                        rows.append(r)
        data['values_list_headers'] = headers
        data['values_list'] = rows

    def to_representation(self, obj):
        data = super(
            DBLayerFieldSerializer, self).to_representation(obj)

        data['null'] = obj.null
        data['size'] = obj.size
        data['decimals'] = obj.decimals
        data['widget'] = obj.widget
        getattr(self, '_serialize_%s' % obj.widget, self._serialize_auto)(obj, data)
        return data

    class Meta:
        model = DataBaseLayerField
        fields = ['name', 'label', 'search', 'fullsearch', 'readonly']
        list_serializer_class = DBLayerFieldListSerializer
