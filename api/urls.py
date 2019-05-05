from django.conf.urls import url
from .views import CreateUserAPIView, authenticate_user, get_all_contests, get_contest
app_name = 'api'

urlpatterns = [
    url(r'^signup/$', CreateUserAPIView.as_view()),
    url(r'^login/$', authenticate_user),
]

extrapatterns = [
    url(r'^$', get_all_contests),
    url(r'^(?P<contest_id>\d{1})$', get_contest)
]
