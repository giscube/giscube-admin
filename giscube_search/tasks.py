from giscube.celery import app


from celery_progress.backend import ProgressRecorder


def giscube_search_rebuild_index(task=None):
    from django.core.management import call_command
    progress_recorder = ProgressRecorder(task) if task else None
    call_command("giscube_search_rebuild_index")
    progress_recorder.set_progress(1, 1)


@app.task(queue='sequential_queue', bind=True)
def async_giscube_search_rebuild_index(self):
    giscube_search_rebuild_index(self)

