from django import template
from django.conf import settings
from django.urls import reverse

register = template.Library()


@register.inclusion_tag('giscube/tags/admin_tasks_menu.html', takes_context=True)
def admin_tasks_menu(context):
    items = []
    for task in settings.ADMIN_TASKS_MENU:
        url = task.get('url')
        if task.get('reverse', False):
            url = reverse(url)
        item = {'title': task.get('title'), 'url': url}
        items.append(item)
    return {
        'items': items
    }
