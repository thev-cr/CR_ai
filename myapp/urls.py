from django.urls import path
from .views import predict, home_view

urlpatterns = [
    path('predict/', predict, name='predict'),
    path('', home_view),
]
