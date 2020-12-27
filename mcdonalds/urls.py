from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('stores_contact/',views.stores_contact, name='stores_contact'),
    path('suppliers_contact/',views.suppliers_contact, name='suppliers_contact'),
    path('raw_materials/als_predict/',views.raw_materials_predict, name='raw_materials_predict'),
    path('raw_materials_order/',views.raw_materials_order, name='raw_materials_order'),
    path('raw_materials/',views.raw_materials, name='raw_materials'),
    path('strategies_list/', views.strategies_list, name='strategies_list'),
    path('strategy/add/', views.add_strategy, name='add_strategy'),
    path('strategy/update/<int:strategy_id>/', views.update_strategy, name='update_strategy'),
    path('strategy/delete/<int:strategy_id>/', views.delete_strategy, name='delete_strategy'),
    path('customer_rel/binary_tree/', views.binary_tree, name='binary_tree'),
    path('customer_rel/survival_rate/', views.survival_rate, name='survival_rate'),
    path('customer_rel/rfm/', views.rfm, name='rfm'),
    path('customer_rel/rfm/<int:rfm_id>', views.customer, name='customer'),
    path('edit/<int:material_id>/', views.get_edit_page, name='get_edit_page'),
    path('update/<int:material_id>/', views.save_update_raw_materials, name='save_update_raw_materials'),
    path('send_store_demend', views.receive_store_demand, name='receive_store_demand'),
    path('go_to_store_send_demand_page',views.go_to_store_send_demand_page, name='go_to_store_send_demand_page'),
    path('orders/add/', views.add_order, name='add_order'),
    path('store_demand', views.store_demand, name='store_demand'),
]
app_name='mcdonalds'
