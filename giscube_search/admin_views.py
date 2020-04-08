from django.views.generic import TemplateView

from .tasks import async_giscube_search_rebuild_index


class RebuildGiscubeSearchIndexView(TemplateView):
    template_name = 'admin/giscube_search/rebuild_giscube_search_index.html'

    def dispatch(self, *args, **kwargs):
        self.task = async_giscube_search_rebuild_index.delay()
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.task:
            context['task'] = {'task_id': self.task.task_id}
        return context
