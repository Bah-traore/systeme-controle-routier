"""URLs de l'application Identité."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = 'identite'

router = DefaultRouter()
router.register('utilisateurs', views.UtilisateurViewSet, basename='utilisateur')

urlpatterns = [
    # Authentification
    path('login/', views.LoginView.as_view(), name='login'),
    path('mfa/verify/', views.MFAVerifyView.as_view(), name='mfa-verify'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('me/', views.MeView.as_view(), name='me'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # CRUD utilisateurs
    path('', include(router.urls)),
]
