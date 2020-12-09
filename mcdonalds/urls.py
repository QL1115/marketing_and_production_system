from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('stores_detail',views.stores_detail)
]