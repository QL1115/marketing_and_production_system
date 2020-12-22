from django.urls import path

from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('stores_contact',views.stores_contact),
    path('suppliers_contact',views.suppliers_contact),
    path('raw_materials_predict',views.raw_materials_predict),
    path('raw_materials_order',views.raw_materials_order),
    path('raw_materials',views.raw_materials),
    path('edit/<int:material_id>', views.get_edit_page),  
    path('update/<int:material_id>', views.save_update),  
]
