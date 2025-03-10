from django.contrib import admin
from django.http import HttpResponse
from django.utils.translation import gettext as _
from tablib import Dataset as TablibDataset


@admin.action(description=_("Download selected visor users (CSV)"))
def download_visor_csv(modeladmin, request, queryset):
    headers = ('username', 'ip', 'datetime')
    data = TablibDataset(headers=headers)

    for layer in queryset:
        data.append([
            layer.username,
            layer.ip,
            layer.datetime
        ])

    response = HttpResponse(data.export('csv'), 'text/csv')
    response['Content-Disposition'] = 'attachment; filename="VisorUserTrack.csv"'
    return response


@admin.action(description=_("Download selected registers (CSV)"))
def download_layers_csv(modeladmin, request, queryset):
    headers = ('layer_name', 'giscube_id', 'datetime', 'username')
    data = TablibDataset(headers=headers)

    for layer in queryset:
        data.append([
            layer.layer_name,
            layer.giscube_id,
            layer.datetime,
            layer.username
        ])

    response = HttpResponse(data.export('csv'), 'text/csv')
    response['Content-Disposition'] = 'attachment; filename="LayersRegister.csv"'
    return response


@admin.action(description=_("Download selected registers (CSV)"))
def download_tools_csv(modeladmin, request, queryset):
    headers = ('tool_name', 'datetime', 'username')
    data = TablibDataset(headers=headers)

    for layer in queryset:
        data.append([
            layer.tool_name,
            layer.datetime,
            layer.username
        ])

    response = HttpResponse(data.export('csv'), 'text/csv')
    response['Content-Disposition'] = 'attachment; filename="ToolsRegister.csv"'
    return response
