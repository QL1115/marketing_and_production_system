from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import connection

from .utils.RawFiles import delete_uploaded_file,get_uploaded_file


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


@require_http_methods(["DELETE"])
@csrf_exempt # TODO: for test，若未加這行，使用 postman 測試 post 時，會報 403，因為沒有 CSRF token
def delete_file(request, comp_id, rpt_id, acc_id, table_name):
    result = delete_uploaded_file(rpt_id, table_name)
    return HttpResponse(result) # TODO: for test


def get_import_page(request,comp_id, rpt_id, acc_id):

    #執行原生sql，查詢CashInBanks是否已經有匯入
    cursor1 = connection.cursor()
    cursor1.execute("select count(*) from `Group` inner join Company on `Group`.grp_id=Company.grp_id inner join Report on Company.com_id=Report.com_id inner join CashInBanks on Report.rpt_id=CashInBanks.rpt_id WHERE Report.rpt_id = %s", [rpt_id])
    count_CashInBank = cursor1.fetchone()

    #執行原生sql，查詢Depositaccount是否已經有匯入
    cursor2 = connection.cursor()
    cursor2.execute("select count(*) from `Group` inner join Company on `Group`.grp_id=Company.grp_id inner join Report on Company.com_id=Report.com_id inner join Depositaccount on Report.rpt_id=Depositaccount.rpt_id WHERE Report.rpt_id = %s", [rpt_id])
    count_Depositaccount = cursor2.fetchone()

    if count_CashInBank[0]>0 and count_Depositaccount[0]>0:
        #銀行存款跟定期存款皆已匯入資料
        pass
    elif count_CashInBank[0]>0 and count_Depositaccount[0]==0:
        #銀行存款已匯入資料
        pass
    elif count_Depositaccount[0]>0 and count_CashInBank[0]==0:
        #定期存款已匯入資料
        pass
    else:
        pass


    return render (request,'import_page.html',{ 'acc_id': acc_id})
