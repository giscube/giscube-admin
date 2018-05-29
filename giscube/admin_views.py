from django.views.generic import TemplateView

from giscube.tasks import async_haystack_rebuild_index


class RebuildIndexView(TemplateView):
    template_name = 'admin/giscube/rebuild_index.html'

    def dispatch(self, *args, **kwargs):
        self.task = async_haystack_rebuild_index.delay()
        return super(RebuildIndexView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(RebuildIndexView, self).get_context_data(**kwargs)
        if self.task:
            context['task'] = {'task_id': self.task.task_id}
        return context
