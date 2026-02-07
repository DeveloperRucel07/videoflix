from django.urls import path
from auth_app.api.views import ActivateAccountView, CookieTokenObtainPairView, RegistrationView

urlpatterns = [
    path('register/', RegistrationView.as_view(), name='register'),
    path('activate/<uidb64>/<token>/', ActivateAccountView.as_view(), name='activate'),
    path('login/', CookieTokenObtainPairView.as_view(), name='login'),
]