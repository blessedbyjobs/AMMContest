from django.conf.urls import url
from .views import CreateUserAPIView, authenticate_user, get_all_contests, get_contest, participate, get_tasks, get_task, send, my_results
app_name = 'api'

urlpatterns = [
    url(r'^signup/$', CreateUserAPIView.as_view()),
    url(r'^login/$', authenticate_user),
]

extrapatterns = [
    url(r'^$', get_all_contests),
    url(r'^(?P<contest_id>\d{1})$', get_contest),
    url(r'^(?P<contest_id>\d{1})/participate$', participate),
    url(r'^(?P<contest_id>\d{1})/tasks$', get_tasks),
    url(r'^(?P<contest_id>\d{1})/tasks/(?P<task_id>\d{1})$', get_task),
    url(r'^(?P<contest_id>\d{1})/tasks/(?P<task_id>\d{1})/send$', send),
    url(r'^(?P<contest_id>\d{1})/tasks/(?P<task_id>\d{1})/myresults$', my_results),
]
