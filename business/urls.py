from django.urls import path, include
from rest_framework import routers

from business import views

router = routers.DefaultRouter()
router.register('file', views.FileViewSet)
router.register('task', views.TaskViewSet)
router.register('evaluate', views.TrafficStateEtaViewSet)
router.register('map_matching', views.MapMatchingViewSet)
router.register('traj_loc', views.TrajLocPredViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
