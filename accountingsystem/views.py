from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .utils.RawFiles import delete_uploaded_file, check_and_save_cash_in_banks,check_and_save_deposit_account, get_uploaded_file
from django.db import connection
import xlrd # xlrd 方法參考：https://blog.csdn.net/wangweimic/article/details/87344803

def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

@require_http_methods(["DELETE"])
@csrf_exempt # TODO: for test，若未加這行，使用 postman 測試 post 時，會報 403，因為沒有 CSRF token
def delete_file(request, comp_id, rpt_id, acc_id, table_name):
    delete_uploaded_file(rpt_id, table_name)
    return HttpResponse({"status_code": 200, "msg":"成功刪除檔案"})

@require_http_methods(["POST"])
@csrf_exempt
def upload_file(request, comp_id, rpt_id, acc_id, table_name):
    '''上傳銀行存款'''
    # 1. 檢查檔案類型是否為 excel
    # 2. 檢查檔案是否僅有1個分頁
    # 3. 呼叫 check_and_save 方法，進入檢查流程
    print('upload_file() >>> start')
    try:
        # file = request.FILES.('file')
        file = request.FILES["file"]
        print('request >>>>>>', request)
        book = xlrd.open_workbook(file.name, file_contents=file.read())
        print('book >>>', book)

        if book.nsheets != 1:
            return {"status_code": 422, "msg":"檔案超過一個分頁。", "redirect_url":" "}
        # TODO 之後可以對上傳的檔案新增更多的基本檢查

        sheet = book.sheets()[0]
        if table_name == "cash_in_bank":
            result = check_and_save_cash_in_banks(rpt_id, sheet)
            return result
        elif table_name == "deposit_account":
            result = check_and_save_deposit_account(rpt_id, sheet)
            return result

        else:
            return {"status_code": 500, "msg": "發生不明錯誤。"}

    except Exception as e:
        print('upload_file exception >>> ', e)
        # return HttpResponseRedirect('{"status_code": 500, "msg": "發生不明錯誤。"}')
        return {"status_code": 500, "msg": "發生不明錯誤。"}


@require_http_methods(["DELETE"])
@csrf_exempt # TODO: for test，若未加這行，使用 postman 測試 post 時，會報 403，因為沒有 CSRF token
def delete_file(request, comp_id, rpt_id, acc_id, table_name):
    result = delete_uploaded_file(rpt_id, table_name)
    return HttpResponse(result) # TODO: for test

@csrf_exempt
def get_import_page(request,comp_id, rpt_id, acc_id):

    if request.method == 'GET':
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

        return render(request, 'import_page.html',{ 'acc_id': acc_id,
                                                    'comp_id': comp_id,
                                                    'rpt_id': rpt_id })
    elif request.method == 'POST':
        table_name = request.POST.get('table_name')
        print('table_name >>> ', table_name)
        result = upload_file(request, comp_id, rpt_id, acc_id, table_name)
        print('result >>> ', result)
        return render(request, 'import_page.html', {'acc_id': acc_id,
                                                    'comp_id': comp_id,
                                                    'rpt_id': rpt_id,
                                                    'import_related_list': [result['status_code'], result['msg']]})
