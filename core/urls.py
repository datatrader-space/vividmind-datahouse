from django.urls import path
from .views import consume,sync,provide

from django.urls import path, include

urlpatterns = [
    path("api/consume/", consume, name='consume'),
    path("api/sync/", sync, name='sync'),
    path("api/provide/", provide, name='provide'),
]