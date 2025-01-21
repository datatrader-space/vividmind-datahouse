from django.urls import path
from .views import consume

from django.urls import path, include

urlpatterns = [
    path("api/consume/", consume, name='bulk_campaign'),
]