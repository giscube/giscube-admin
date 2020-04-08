from giscube.celery import app


def giscube_search_rebuild_index():
    from django.core.management import call_command
    call_command('giscube_search_rebuild_index')


@app.task(queue='sequential_queue')
def async_giscube_search_rebuild_index():
    giscube_search_rebuild_index()
