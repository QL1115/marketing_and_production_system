from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('companies/<int:comp_id>/projects/<int:rpt_id>/accounts/<int:acc_id>/raw_files/<str:table_name>', views.delete_file,name="delete_file"),
    #path('companies/<int:comp_id>/projects/<int:rpt_id>/accounts/<int:acc_id>/raw_files/<str:table_name>', views.upload_file,name="upload_file"),
    path('companies/<int:comp_id>/projects/<int:rpt_id>/accounts/<int:acc_id>/import', views.get_import_page, name='import'),
    path('companies/<int:comp_id>/projects/<int:rpt_id>/accounts/<int:acc_id>/check', views.get_check_page, name='check_page'),
    path('companies/<int:comp_id>/projects/<int:rpt_id>/accounts/<int:acc_id>/raw_files/update/<str:table_name>', views.update_raw_file, name='update_raw_file'),
    path('companies/<int:com_id>/projects/<int:rpt_id>/accounts/<int:acc_id>/adjust_acc_all', views.adjust_acc_all, name='adjust_acc_all'),
]

