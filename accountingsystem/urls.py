from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('companies/<int:comp_id>/projects/<int:rpt_id>/accounts/<int:acc_id>/raw_files/<str:table_name>', views.delete_file,name="delete_file"),
    #path('companies/<int:comp_id>/projects/<int:rpt_id>/accounts/<int:acc_id>/raw_files/<str:table_name>', views.upload_file,name="upload_file"),
    path('companies/<int:comp_id>/projects/<int:rpt_id>/accounts/<int:acc_id>/import', views.get_import_page, name='import'),
    path('companies/<int:comp_id>/projects/<int:rpt_id>/accounts/<int:acc_id>/check', views.get_check_page, name='check_page'),
    path('companies/<int:comp_id>/projects/<int:rpt_id>/accounts/<int:acc_id>/raw_files/update/<str:table_name>', views.update_raw_file, name='update_raw_file'),
    path('companies/<int:comp_id>/projects/<int:rpt_id>/accounts/<int:acc_id>/adjust_acc', views.adjust_acc, name='adjust_acc'),
    path('companies/<int:comp_id>/new_report', views.new_report, name='new_report'),
    path('companies/<int:comp_id>/dashboard_page', views.get_dashboard_page, name='dash_board'),
    path('companies/<int:comp_id>/projects/<int:rpt_id>/accounts/<int:acc_id>/disclosure', views.get_disclosure_page, name='disclosure_page'),
    path('compaines/<int:comp_id>/consolidated_report', views.consolidated_report, name='consolidated_report'),
    path('companies/<int:comp_id>/projects/<int:rpt_id>/',views.get_consolidated_statement_page, name='get_consolidated_statement_page'),
    path('companies/<int:comp_id>/projects/<int:rpt_id>/disclosure',views.get_consolidated_disclosure_page, name='get_consolidated_disclosure_page'),
    path('companies/<int:comp_id>/projects/<int:rpt_id>/compare_with_last_consolidated_statement',views.compare_with_last_consolidated_statement, name='compare_with_last_consolidated_statement'),
    path('companies/<int:comp_id>/projects/<int:rpt_id>/accounts/<int:acc_id>/previous_comparison',views.previous_comparison, name='previous_comparison'),
]
