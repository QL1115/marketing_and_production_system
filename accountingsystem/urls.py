from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('companies/<int:comp_id>/projects/<int:rpt_id>/accounts/<int:acc_id>/raw_files/<str:table_name>', views.delete_file),
    path('companies/<int:comp_id>/projects/<int:rpt_id>/accounts/<int:acc_id>/raw_files', views.upload_cash_in_bank),
]