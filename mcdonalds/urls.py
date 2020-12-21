from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('stores_detail/',views.stores_detail, name='stores_detail'),
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
    path('edit/<int:material_id>/', views.get_edit_page, name='get_edit_page'),
    path('update/<int:material_id>/', views.save_update, name='save_update'),
]
app_name='mcdonalds'
