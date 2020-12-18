from django.urls import path

from . import views
app_name = 'mcdonalds'
urlpatterns = [
    path('', views.index, name='index'),
    path('stores_detail',views.stores_detail),
    path('raw_materials_predict',views.raw_materials_predict),
    path('raw_materials_order',views.raw_materials_order),
    path('raw_materials',views.raw_materials),
    path('update/＜int:pk＞', views.update_raw_materials, name='update')
]
