
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from pandas._libs import json
from .utils.Entries import create_preamount_and_adjust_entries_for_project_account
from .utils.RawFiles import delete_uploaded_file, check_and_save_cash_in_banks,check_and_save_deposit_account, get_uploaded_file
from django.db import connection
from .models import Cashinbanks, Depositaccount
from .forms import CashinbanksForm, DepositAccountForm
import xlrd # xlrd 方法參考：https://blog.csdn.net/wangweimic/article/details/87344803


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

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

#@require_http_methods(["DELETE"])
@csrf_exempt # TODO: for test，若未加這行，使用 postman 測試 post 時，會報 403，因為沒有 CSRF token
def delete_file(request, comp_id, rpt_id, acc_id, table_name):
    # print('del')
    # delete_uploaded_file(rpt_id, table_name)
    # return HttpResponse({"status_code": 
    # 
    # , "msg":"成功刪除檔案"})
    print('in_del!!!!!!!!!!')
    try:
        delete_uploaded_file(rpt_id, table_name)
    except:
        pass

def check(rpt_id):
    #執行原生sql，查詢CashInBanks是否已經有匯入
    cursor1 = connection.cursor()
    cursor1.execute("select count(*) from `Group` inner join Company on `Group`.grp_id=Company.grp_id inner join Report on Company.com_id=Report.com_id inner join CashInBanks on Report.rpt_id=CashInBanks.rpt_id WHERE Report.rpt_id = %s", [rpt_id])
    count_CashInBank = cursor1.fetchone()

    #執行原生sql，查詢Depositaccount是否已經有匯入
    cursor2 = connection.cursor()
    cursor2.execute("select count(*) from `Group` inner join Company on `Group`.grp_id=Company.grp_id inner join Report on Company.com_id=Report.com_id inner join Depositaccount on Report.rpt_id=Depositaccount.rpt_id WHERE Report.rpt_id = %s", [rpt_id])
    count_Depositaccount = cursor2.fetchone()
    print('~~~~~~~!!!!!!!!!!')

    if count_CashInBank[0]>0:
        #銀行存款已匯入資料
        count_CashInBank_result={"status_code": 123, "msg": "銀行存款已匯入資料"}
            
    else:
        #銀行存款沒有
        count_CashInBank_result={"status_code": 456, "msg": "銀行存款沒匯入過"}
            

    if count_Depositaccount[0]>0:
        #定期存款已匯入資料
        count_Depositaccount_result={"status_code": 789, "msg": "定期存款已匯入資料"}
    else:
        #定期存款沒有
        count_Depositaccount_result={"status_code": 999, "msg": "定期存款沒匯入過"}
    return(count_CashInBank_result,count_Depositaccount_result)

@csrf_exempt
def get_import_page(request,comp_id, rpt_id, acc_id):

    print('into get_import')
    if request.method == 'GET':
        check(rpt_id)
        print('checccccccccccck',check(rpt_id))
        print(type(check(rpt_id)))
        count_CashInBank_result=check(rpt_id)[0]
        print()
        count_Depositaccount_result=check(rpt_id)[1]


        
        return render(request, 'import_page.html',{ 'acc_id': acc_id,
                                                    'comp_id': comp_id,
                                                    'rpt_id': rpt_id ,
                                                    'count_CashInBank_list': [count_CashInBank_result['status_code'], count_CashInBank_result['msg']],
                                                    'count_Depositaccount_list':[count_Depositaccount_result['status_code'], count_Depositaccount_result['msg']]
                                                    })
    elif request.method == 'POST':
        table_name = request.POST.get('table_name')
        print('table_name >>> ', table_name)
        result = upload_file(request, comp_id, rpt_id, acc_id, table_name)
        print('result >>> ', result)
        print(type(result))
        print(result['status_code'])
        print(type(result['status_code']))
        check(rpt_id)
        count_CashInBank_result=check(rpt_id)[0]
        count_Depositaccount_result=check(rpt_id)[1]
       
        #如果兩張表都已經匯入，才進行建立分錄
        if check(rpt_id)[0]['status_code']==123 and check(rpt_id)[1]['status_code']==789:
            #建立分錄，此method放在utils的Entries中
            create_preamount_and_adjust_entries_for_project_account(comp_id, rpt_id, acc_id)


        return render(request, 'import_page.html', {'acc_id': acc_id,
                                                    'comp_id': comp_id,
                                                    'rpt_id': rpt_id,
                                                    'import_related_list': [result['status_code'], result['msg']],
                                                    'count_CashInBank_list': [count_CashInBank_result['status_code'], count_CashInBank_result['msg']],
                                                    'count_Depositaccount_list':[count_Depositaccount_result['status_code'], count_Depositaccount_result['msg']]
                                                    })

def get_check_page(request, comp_id, rpt_id, acc_id):
    table_name = 'cash_in_banks'
    uploadFile = get_uploaded_file(rpt_id, table_name)
    cibSummary = 0
    cibData = {}
    if uploadFile.get('status_code') == 200:
        cibData = uploadFile.get('returnObject')
        for i in cibData:
            cibSummary += int(i.ntd_amount)

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
        return render(request, 'checking_page.html', {'comp_id': comp_id, 'rpt_id':rpt_id, 'acc_id':acc_id, 'msg':msg})
    return render(request, 'checking_page.html', {'comp_id': comp_id, 'rpt_id':rpt_id, 'acc_id': acc_id, 'cibData': cibData, 'depositData':depositData,
                                                 'cibSummary': cibSummary, 'depositSummary':depositSummary})
@csrf_exempt
def update_raw_file(request, comp_id, rpt_id, acc_id, table_name):
    if request.method == 'POST' and request.is_ajax():
        # ⚠️ 注意：若是用 Ajax 以 JSON 格式， POST 方式送 data 過來，這裡使用 request.body 來接收並且需要處理一下 json。
        data = json.loads(request.body) #
        # print("data >>> ", data)
        if table_name == 'cash_in_banks':
            form = CashinbanksForm(data)
            if form.is_valid():
                cash_in_banks = Cashinbanks.objects.get(cash_in_banks_id=data.get('id'))
                form = CashinbanksForm(data, instance=cash_in_banks)
                form.save()
                context = {
                    'table_name': 'cash_in_banks',
                    'isUpdated': True
                }
                return JsonResponse(context)
            else:
                return JsonResponse({
                    'table_name': 'cash_in_banks',
                    'isUpdated': False
                })
        elif table_name == 'deposit_account':
            form = DepositAccountForm(data)
            if form.is_valid():
                deposit_account = Depositaccount.objects.get(dep_acc_id=data.get('id'))
                form = DepositAccountForm(data, instance=deposit_account)
                form.save()
                context = {
                    'table_name': 'deposit_account',
                    'isUpdated': True
                }
                return JsonResponse(context)
            else:
                return JsonResponse({
                    'table_name': 'deposit_account',
                    'isUpdated': False
                })