import os

from django import forms
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.views.generic import TemplateView

from imageserver.gdal_utils import gdal_build_overviews


class OptimizerEntry(object):
    def __init__(self):
        self.type = None
        self.name = '-'


class ActionForm(forms.Form):
    action = forms.CharField(max_length=30)
    path = forms.CharField(max_length=255, required=False)


class RasterOptimizerView(TemplateView):
    template_name = "admin/imageserver/raster_optimizer.html"
    form = ActionForm

    def __init__(self):
        # FIXME: support for multiple directories
        print('DIR', settings.GISCUBE_IMAGESERVER['DATA_ROOT'][0])
        self.storage = FileSystemStorage(
            settings.GISCUBE_IMAGESERVER['DATA_ROOT'][0])

    def get_context_data(self, **kwargs):
        context = super(RasterOptimizerView, self).get_context_data(**kwargs)

        dir = self.request.GET.get('dir', '')
        context['dir'] = dir
        if dir.startswith('/'):
            dir = dir[1:]

        dirs, files = self.storage.listdir(dir)
        entries = []
        for f in sorted(dirs):
            e = OptimizerEntry()
            e.name = f
            e.type = 'folder'
            e.path = os.path.join(dir, f)
            entries.append(e)

        for f in sorted(files):
            e = OptimizerEntry()
            e.name = f
            e.type = 'file'
            e.path = os.path.join(dir, f)

            try:
                e.size = self.storage.size(e.path)
            except Exception:
                e.size = 0

            for format in ('.tif', '.jpg'):
                if f.lower().endswith(format):
                    e.overview = True
            entries.append(e)

        context['entries'] = entries

        return context

    def post(self, request, *args, **kwargs):
        f = self.form(request.POST)
        if f.is_valid():
            action = f.cleaned_data['action']
            path = f.cleaned_data['path']
            if action == 'delete':
                self.storage.delete(path)
            elif action == 'build_overviews':
                gdal_build_overviews(self.storage.path(path))
                return HttpResponse('Overviews completed for %s' % path)
        else:
            return HttpResponse(f.errors)
        return HttpResponse('OK')
