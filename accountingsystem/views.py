from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .utils.RawFiles import delete_uploaded_file, check_and_save_cash_in_banks, get_uploaded_file
from django.db import connection
import xlrd  # xlrd 方法參考：https://blog.csdn.net/wangweimic/article/details/87344803


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


@require_http_methods(["DELETE"])
@csrf_exempt  # TODO: for test，若未加這行，使用 postman 測試 post 時，會報 403，因為沒有 CSRF token
def delete_file(request, comp_id, rpt_id, acc_id, table_name):
    delete_uploaded_file(rpt_id, table_name)
    return HttpResponse({"status_code": 200, "msg":"成功刪除檔案"})


@require_http_methods(["POST"])
@csrf_exempt
def upload_cash_in_bank(request, comp_id, rpt_id):  # TODO: check 的時候給 acc_id 才對?
    '''上傳銀行存款'''
    # 1. 檢查檔案類型是否為 excel
    # 2. 檢查檔案是否僅有1個分頁
    # 3. 呼叫 check_and_save 方法，進入檢查流程
    try:
        cash_in_banks_sheet = xlrd.open_workbook("銀行存款.xlsx")  # TODO: 檔名待討論
    except Exception as e:
        print('upload_cash_in_bank >>> ', e)
        return '{"status_code": 500, "msg": "檔案類型非xlsx，或發生不明錯誤。"}'
    if cash_in_banks_sheet.nsheets != 1:
        return '{"status_code": 422, "msg":"檔案超過一個分頁。", "redirect_url":" "}'
        check_and_save_cah_in_banks(rpt_id, cash_in_banks_sheet)
    return HttpResponse({"status_code": 200, "msg":"成功上傳銀行存款"})


@require_http_methods(["POST"])
@csrf_exempt
def upload_deposit_account(request, comp_id, rpt_id):
    try:
        deposit_account_sheet = xlrd.open_workbook("定期存款.xlsx")  # TODO: 檔名待討論
    except Exception as e:
        print('upload_deposit_account >>> ', e)
        return '{"status_code": 500, "msg": "檔案類型非xlsx，或發生不明錯誤。"}'
    if deposit_account_sheet.nsheets != 1:
        return '{"status_code": 422, "msg":"檔案超過一個分頁。", "redirect_url":" "}'
    # check_and_save_deposit_account(rpt_id, deposit_account_sheet);
    return HttpResponse({"status_code": 200, "msg":"成功上傳定期存款"})


def get_import_page(request, comp_id, rpt_id, acc_id):

    # 執行原生sql，查詢CashInBanks是否已經有匯入
    cursor1 = connection.cursor()
    cursor1.execute("select count(*) from `Group` inner join Company on `Group`.grp_id=Company.grp_id inner join Report on Company.com_id=Report.com_id inner join CashInBanks on Report.rpt_id=CashInBanks.rpt_id WHERE Report.rpt_id = %s", [rpt_id])
    count_CashInBank = cursor1.fetchone()

    # 執行原生sql，查詢Depositaccount是否已經有匯入
    cursor2 = connection.cursor()
    cursor2.execute("select count(*) from `Group` inner join Company on `Group`.grp_id=Company.grp_id inner join Report on Company.com_id=Report.com_id inner join Depositaccount on Report.rpt_id=Depositaccount.rpt_id WHERE Report.rpt_id = %s", [rpt_id])
    count_Depositaccount = cursor2.fetchone()

    if count_CashInBank[0] > 0 and count_Depositaccount[0] > 0:
        # 銀行存款跟定期存款皆已匯入資料
        pass
    elif count_CashInBank[0] > 0 and count_Depositaccount[0] == 0:
        # 銀行存款已匯入資料
        pass
    elif count_Depositaccount[0] > 0 and count_CashInBank[0] == 0:
        # 定期存款已匯入資料
        pass
    else:
        pass

    return render (request, 'import_page.html', { 'acc_id': acc_id})

def get_check_page(request, comp_id, rpt_id, acc_id):
    table_name = 'cash_in_banks'
    uploadFile = get_uploaded_file(rpt_id, table_name)
    cibSummary = 0
    if uploadFile.get('status_code') == 200:
        cibData = uploadFile.get('returnObject')
        for i in cibData:
            cibSummary += (i.ntd_amount)
    else:
        msg = uploadFile.get('msg')

    table_name = 'deposit_account'
    uploadFile = get_uploaded_file(rpt_id, table_name)
    depositSummary = 0
    if uploadFile.get('status_code') == 200:
        depositData = uploadFile.get('returnObject')
        # cauclate summary

        for i in depositData:
            depositSummary += int(i.ntd_amount)
    else:
        msg = uploadFile.get('msg')
        # 這裡要傳errorPage回去嗎
        return render(request, 'checking_page.html', {'acc_id':acc_id, 'msg':msg})
    return render(request, 'checking_page.html', {'acc_id': acc_id, 'cibData': cibData, 'depositData':depositData,
                                                 'cibSummary':cibSummary, 'depositSummary':depositSummary})

