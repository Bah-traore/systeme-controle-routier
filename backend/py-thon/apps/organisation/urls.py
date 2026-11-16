"""URLs de l'application Organisation."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'organisation'

router = DefaultRouter()
router.register('structures', views.StructureAdministrativeViewSet, basename='structure')
router.register('zones', views.ZoneControleViewSet, basename='zone')
router.register('permissions', views.PermissionViewSet, basename='permission')
router.register('roles', views.RoleViewSet, basename='role')
router.register('affectations', views.AffectationViewSet, basename='affectation')

urlpatterns = [
    path('', include(router.urls)),
]
