import django.dispatch


service_project_updated = django.dispatch.Signal(providing_args=['sender', 'obj'])

service_updated = django.dispatch.Signal(providing_args=['sender', 'obj'])
