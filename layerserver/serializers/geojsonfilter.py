from rest_framework import serializers

from layerserver.models import GeoJsonFilter

from giscube_search.utils import remove_accents


class GeoJSONFilterSerializer(serializers.ModelSerializer):
    color = serializers.SerializerMethodField()
    icon = serializers.SerializerMethodField()

    class Meta:
        model = GeoJsonFilter
        fields = ['title', 'description', 'filter', 'color', 'icon']

    def get_color(self, obj):
        color = obj.layer.stroke_color or obj.layer.fill_color or obj.layer.icon_color
        if obj.layer.rules:
            for rule in obj.layer.rules.all():
                if rule.value and obj.title and remove_accents(rule.value.lower()) in remove_accents(obj.title.lower()):
                    rule_color = rule.stroke_color or rule.fill_color or rule.icon_color
                    if rule_color == None or rule_color == '':
                        return color
                    else:
                        return rule_color
        return color

    def get_icon(self, obj):
        icon = f"{obj.layer.icon_type} {obj.layer.icon}" if obj.layer.icon_type else obj.layer.icon
        if obj.layer.rules:
            for rule in obj.layer.rules.all():
                if rule.value and obj.title and remove_accents(rule.value.lower()) in remove_accents(obj.title.lower()):
                    rule_icon = f"{rule.icon_type} {rule.icon}" if rule.icon_type else rule.icon
                    if rule_icon == None or rule_icon == '':
                        return icon
                    else:
                        return rule_icon
        return icon
