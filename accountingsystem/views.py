from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import xlrd # xlrd 方法參考：https://blog.csdn.net/wangweimic/article/details/87344803

from .utils.RawFiles import delete_uploaded_file, check_and_save_cash_in_banks


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

@require_http_methods(["DELETE"])
@csrf_exempt # TODO: for test，若未加這行，使用 postman 測試 post 時，會報 403，因為沒有 CSRF token
def delete_file(request, comp_id, rpt_id, acc_id, table_name):
    delete_uploaded_file(rpt_id, table_name)
    return HttpResponse({"status_code": 200, "msg":"成功刪除檔案"})

@require_http_methods(["POST"])
@csrf_exempt
def upload_cash_in_bank(request, comp_id, rpt_id): # TODO: check 的時候給 acc_id 才對?
    '''上傳銀行存款'''
    # 1. 檢查檔案類型是否為 excel
    # 2. 檢查檔案是否僅有1個分頁
    # 3. 呼叫 check_and_save 方法，進入檢查流程
    try:
        cash_in_banks_sheet = xlrd.open_workbook("銀行存款.xlsx") # TODO: 檔名待討論
    except Exception as e:
        print('upload_cash_in_bank >>> ', e)
        return '{"status_code": 500, "msg": "檔案類型非xlsx，或發生不明錯誤。"}'
    if cash_in_banks_sheet.nsheets != 1:
        return '{"status_code": 422, "msg":"檔案超過一個分頁。", "redirect_url":" "}'
        check_and_save_cah_in_banks(rpt_id, cash_in_banks_sheet.sheet_by_index(0))
    return HttpResponse({"status_code": 200, "msg":"成功上傳銀行存款"})

@require_http_methods(["POST"])
@csrf_exempt
def upload_deposit_account(request, comp_id, rpt_id):
    try:
        deposit_account_sheet = xlrd.open_workbook("定期存款.xlsx") # TODO: 檔名待討論
    except Exception as e:
        print('upload_deposit_account >>> ', e)
        return '{"status_code": 500, "msg": "檔案類型非xlsx，或發生不明錯誤。"}'
    if deposit_account_sheet.nsheets != 1:
        return '{"status_code": 422, "msg":"檔案超過一個分頁。", "redirect_url":" "}'
    #check_and_save_deposit_account(rpt_id, deposit_account_sheet.sheet_by_index(0));
    return HttpResponse({"status_code": 200, "msg":"成功上傳定期存款"})

def get_import_page(request,comp_id, rpt_id, acc_id):
    return render (request,'<<匯入頁面 HTML 位置>>',{ 'acc_id': acc_id})

