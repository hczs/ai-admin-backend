from django.urls import path, include
from rest_framework import routers

from business import views

router = routers.DefaultRouter()
router.register('file', views.FileViewSet)
router.register('task', views.TaskViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
