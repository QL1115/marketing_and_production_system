from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('stores_contact/',views.stores_contact, name='stores_contact'),
    path('stores_contact/add/', views.add_stores_contact, name='add_stores_contact'),
    path('stores_contact/update/<int:store_id>/', views.update_stores_contact, name='update_stores_contact'),
    path('stores_contact/delete/<int:store_id>/', views.delete_stores_contact, name='delete_stores_contact'),
    path('suppliers_contact/',views.suppliers_contact, name='suppliers_contact'),
    path('suppliers_contact/add/', views.add_suppliers_contact, name='add_suppliers_contact'),
    path('suppliers_contact/<int:suppliers_id>/', views.update_suppliers_contact, name='update_suppliers_contact'),
    path('suppliers_contact/delete/<int:suppliers_id>/', views.delete_suppliers_contact, name='delete_suppliers_contact'),
    path('raw_materials/als_predict/',views.raw_materials_predict, name='raw_materials_predict'),
    path('raw_materials_order/',views.raw_materials_order, name='raw_materials_order'),
    path('raw_materials/',views.raw_materials, name='raw_materials'),
    path('strategies_list/', views.strategies_list, name='strategies_list'),
    path('strategy/store/', views.store_strategy, name='store_strategy'),
    # path('strategy/update/<int:strategy_id>/', views.update_strategy, name='update_strategy'),
    path('strategy/delete/<int:strategy_id>/', views.delete_strategy, name='delete_strategy'),
    path('strategy_prod/delete/<int:spr_id>', views.delete_spr, name='delete_spr'),
    path('products/<int:prod_category_num>', views.search_prod_by_category, name='search_prod_by_category'),
    # path('customer_rel/binary_tree/', views.binary_tree, name='binary_tree'),
    path('customer_rel/survival_rate/', views.survival_rate, name='survival_rate'),
    path('customer_rel/rfm/', views.rfm, name='rfm'),
    path('customer_rel/rfm/<int:rfm_id>', views.customer, name='customer'),
    path('edit/<int:material_id>/', views.get_edit_page, name='get_edit_page'),
    path('update/<int:material_id>/', views.save_update_raw_materials, name='save_update_raw_materials'),
    path('send_store_demend', views.receive_store_demand, name='receive_store_demand'),
    path('go_to_store_send_demand_page',views.go_to_store_send_demand_page, name='go_to_store_send_demand_page'),
    path('orders/add/', views.add_order, name='add_order'),
    path('store_demand/', views.store_demand, name='store_demand'),
    path('raw_material_arrived_store/<int:store_demand_id>', views.raw_material_arrived_store, name='raw_material_arrived_store'),
    path('raw_material_arrived_center/<int:order_id>', views.raw_material_arrived_center, name='raw_material_arrived_center'),
    path('login/', views.sign_in, name='Login')
]
app_name='mcdonalds'
