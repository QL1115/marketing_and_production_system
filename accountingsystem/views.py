import math
import xlrd  # xlrd 方法參考：https://blog.csdn.net/wangweimic/article/details/87344803
# from datetime import datetime
from datetime import datetime
from django.core.serializers import serialize
from django.db import connection
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from pandas._libs import json

from .forms import CashinbanksForm, DepositAccountForm
from .models import Cashinbanks, Depositaccount, Adjentry, Preamt, Exchangerate, Report, Account, Company, Reltrx, \
    Disclosure, Disdetail, Distitle
from .utils.ConsolidateReport import create_consolidated_report, create_consolidated_report_preamt, \
    delete_consolidate_report
from .utils.Disclosure import delete_disclosure_for_project_account
from .utils.Entries import create_preamount_and_adjust_entries_for_project_account
from .utils.RawFiles import delete_uploaded_file, check_and_save_cash_in_banks, check_and_save_deposit_account, \
    get_uploaded_file
from .utils.PreviousComparison import delete_disdetail_from_previous_comparison, get_current_and_previous_rpt, cal_previous_comparision, search_previous_comparision
from dateutil.relativedelta import relativedelta


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
        book = xlrd.open_workbook(file.name, file_contents=file.read())

        if book.nsheets != 1:
            return {"status_code": 422, "msg": "檔案超過一個分頁。", "redirect_url": " "}
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
    return render(request, 'import_page.html', {'acc_id': acc_id})


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


# @require_http_methods(["DELETE"])
@csrf_exempt  # TODO: for test，若未加這行，使用 postman 測試 post 時，會報 403，因為沒有 CSRF token
def delete_file(request, comp_id, rpt_id, acc_id, table_name):
    # print('del')
    # delete_uploaded_file(rpt_id, table_name)
    # return HttpResponse({"status_code":
    #
    # , "msg":"成功刪除檔案"})
    # delete_preamount(rpt_id, acc_id)
    try:
        delete_uploaded_file(rpt_id, table_name)
        delete_preamount(rpt_id, acc_id)
        delete_consolidate_report(comp_id, rpt_id)
    except Exception as e:
        print('刪除錯誤：', e)


def delete_preamount(rpt_id, acc_id):
    if acc_id == 1:
        delete_cash_preamount(rpt_id)


def delete_cash_preamount(rpt_id):
    print('!!!!in')
    # 全部予以刪除 
    # 必定刪除:1 23 24 25 26
    acc_id = 1
    countIdList = [1, 23, 24, 25, 26]
    deleteAccount = []
    # 抓出全部要被刪除的Account的ID
    for i in countIdList:
        childList = Account.objects.filter(acc_parent=i)
        for a in childList:
            if a.acc_id in countIdList:
                pass
            else:
                countIdList.append(a.acc_id)

    delete_disclosure_for_project_account(acc_id, countIdList, rpt_id)
    # print('執行完了 delete_disclosure_for_project_account')
    for i in countIdList:
        Preamt.objects.filter(rpt=Report.objects.get(rpt_id=rpt_id), acc=Account.objects.get(acc_id=i)).delete()


def check(rpt_id):
    # 執行原生sql，查詢CashInBanks是否已經有匯入
    cursor1 = connection.cursor()
    cursor1.execute(
        "select count(*) from `Group` inner join Company on `Group`.grp_id=Company.grp_id inner join Report on Company.com_id=Report.com_id inner join CashInBanks on Report.rpt_id=CashInBanks.rpt_id WHERE Report.rpt_id = %s",
        [rpt_id])
    count_CashInBank = cursor1.fetchone()

    # 執行原生sql，查詢Depositaccount是否已經有匯入
    cursor2 = connection.cursor()
    cursor2.execute(
        "select count(*) from `Group` inner join Company on `Group`.grp_id=Company.grp_id inner join Report on Company.com_id=Report.com_id inner join Depositaccount on Report.rpt_id=Depositaccount.rpt_id WHERE Report.rpt_id = %s",
        [rpt_id])
    count_Depositaccount = cursor2.fetchone()

    if count_CashInBank[0] > 0:
        # 銀行存款已匯入資料
        count_CashInBank_result = {"status_code": 123, "msg": "銀行存款已匯入資料"}

    else:
        # 銀行存款沒有
        count_CashInBank_result = {"status_code": 456, "msg": "銀行存款沒匯入過"}

    if count_Depositaccount[0] > 0:
        # 定期存款已匯入資料
        count_Depositaccount_result = {"status_code": 789, "msg": "定期存款已匯入資料"}
    else:
        # 定期存款沒有
        count_Depositaccount_result = {"status_code": 999, "msg": "定期存款沒匯入過"}
    return (count_CashInBank_result, count_Depositaccount_result)


@csrf_exempt
def get_import_page(request, comp_id, rpt_id, acc_id):
    if request.method == 'GET':
        check(rpt_id)
        count_CashInBank_result = check(rpt_id)[0]
        count_Depositaccount_result = check(rpt_id)[1]

        return render(request, 'import_page.html', {'acc_id': acc_id,
                                                    'comp_id': comp_id,
                                                    'rpt_id': rpt_id,
                                                    'count_CashInBank_list': [count_CashInBank_result['status_code'],
                                                                              count_CashInBank_result['msg']],
                                                    'count_Depositaccount_list': [
                                                        count_Depositaccount_result['status_code'],
                                                        count_Depositaccount_result['msg']]
                                                    })
    elif request.method == 'POST':
        table_name = request.POST.get('table_name')
        result = upload_file(request, comp_id, rpt_id, acc_id, table_name)
        # print('result >>> ', result)
        # print(type(result))
        # print(result['status_code'])
        # print(type(result['status_code']))
        check(rpt_id)
        count_CashInBank_result = check(rpt_id)[0]
        count_Depositaccount_result = check(rpt_id)[1]

        # 如果兩張表都已經匯入，才進行建立分錄
        if check(rpt_id)[0]['status_code'] == 123 and check(rpt_id)[1]['status_code'] == 789:
            # 建立分錄，此method放在utils的Entries中
            create_preamount_and_adjust_entries_for_project_account(comp_id, rpt_id, acc_id)

        return render(request, 'import_page.html', {'acc_id': acc_id,
                                                    'comp_id': comp_id,
                                                    'rpt_id': rpt_id,
                                                    'import_related_list': [result['status_code'], result['msg']],
                                                    'count_CashInBank_list': [count_CashInBank_result['status_code'],
                                                                              count_CashInBank_result['msg']],
                                                    'count_Depositaccount_list': [
                                                        count_Depositaccount_result['status_code'],
                                                        count_Depositaccount_result['msg']]
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
        return render(request, 'checking_page.html',
                      {'comp_id': comp_id, 'rpt_id': rpt_id, 'acc_id': acc_id, 'msg': msg})
    return render(request, 'checking_page.html',
                  {'comp_id': comp_id, 'rpt_id': rpt_id, 'acc_id': acc_id, 'cibData': cibData,
                   'depositData': depositData,
                   'cibSummary': cibSummary, 'depositSummary': depositSummary})


@csrf_exempt
def update_raw_file(request, comp_id, rpt_id, acc_id, table_name):
    # print('request >>> ', request)
    if request.method == 'POST' and request.is_ajax():
        # ⚠️ 注意：若是用 Ajax 以 JSON 格式， POST 方式送 data 過來，這裡使用 request.body 來接收並且需要處理一下 json。
        data = json.loads(request.body)  #
        # print('unprocessed_data >>>', data)
        data = data['data']
        # print('data >>> ', data)
        # print("data >>> ", data)
        if table_name == 'cash_in_banks':
            for cib_row in data:
                # print('cib_row >>> ', cib_row)
                form = CashinbanksForm(cib_row)
                if form.is_valid():
                    cash_in_banks = Cashinbanks.objects.get(cash_in_banks_id=cib_row.get('id'))
                    form = CashinbanksForm(cib_row, instance=cash_in_banks)
                    form.save()
                else:
                    return JsonResponse({
                        'table_name': 'cash_in_banks',
                        'isUpdated': False
                    })
            delete_preamount(rpt_id, acc_id)
            delete_consolidate_report(comp_id, rpt_id)
            create_preamount_and_adjust_entries_for_project_account(comp_id, rpt_id, acc_id)
            return JsonResponse({
                'table_name': 'cash_in_banks',
                'isUpdated': True
            })

        elif table_name == 'deposit_account':
            for dp_row in data:
                # print('dp_row >>> ', dp_row)
                form = DepositAccountForm(dp_row)
                if form.is_valid():
                    deposit_account = Depositaccount.objects.get(dep_acc_id=dp_row.get('id'))
                    form = DepositAccountForm(dp_row, instance=deposit_account)
                    form.save()
                else:
                    return JsonResponse({
                        'table_name': 'deposit_account',
                        'isUpdated': False
                    })
            delete_preamount(rpt_id, acc_id)
            delete_consolidate_report(comp_id, rpt_id)
            create_preamount_and_adjust_entries_for_project_account(comp_id, rpt_id, acc_id)
            return JsonResponse({
                'table_name': 'deposit_account',
                'isUpdated': True
            })


def adjust_acc(request, comp_id, rpt_id, acc_id):
    """定期存款&銀行存款調整頁"""
    table_name = 'deposit_account'
    uploadFile = get_uploaded_file(rpt_id, table_name)
    if uploadFile.get('status_code') == 200:
        depositData = uploadFile.get('returnObject')
    else:
        msg = uploadFile.get('msg')
        # 這裡要傳errorPage回去嗎
        return render(request, 'adjust_page.html', {'comp_id': comp_id, 'rpt_id': rpt_id, 'acc_id': acc_id, 'msg': msg})
    # 取得分錄(acc_name, amount, adj_num, credit_debit)
    entries = Adjentry.objects.filter(front_end_location=1).select_related('pre__acc').filter(
        pre__rpt_id=rpt_id).values('pre__acc__acc_name',
                                   'amount', 'adj_num',
                                   'credit_debit',
                                   'entry_name')

    entryList = []
    depositEntryList = []
    depositTotalEntryAmountList = []
    depositTotalAmount = 0
    # 先check是否有分錄
    if len(entries) != 0:
        adjNum = entries[0].get('adj_num')
        for entry in entries:
            # 計算調整總額
            if entry.get('pre__acc__acc_name') in entry.get(
                    'entry_name'):  # entry_name不一定會跟adjentry的科目名稱一樣，目前先用contains的方法判斷(待與學姊確定)
                # if entry.get('entry_name') == entry.get('pre__acc__acc_name'):
                # 此分頁的分錄若計在借方都為正，計在貸方都為負
                if entry.get('credit_debit') == 0:
                    amount = entry.get('amount')
                else:
                    amount = -1 * entry.get('amount')
                depositTotalEntryAmountList.append([entry.get('pre__acc__acc_name'), amount])
                depositTotalAmount += amount
            # 同一組就丟進entryList
            if entry.get('adj_num') == adjNum:
                entryList.append(entry)
            # 出現新的adj_num
            else:
                # 先把上一組的entryList丟進depositEntryList
                depositEntryList.append(entryList)
                # 清空entryList
                entryList = []
                entryList.append(entry)
                adjNum = entry.get('adj_num')
        # 把最後一組的entryList丟進depositEntryList
        depositEntryList.append(entryList)
        # 調整合計
        if len(depositTotalEntryAmountList) != 0:
            depositTotalEntryAmountList.append(['合計數', depositTotalAmount])

    table_name = 'cash_in_banks'
    uploadFile = get_uploaded_file(rpt_id, table_name)
    cibData = {}
    if uploadFile.get('status_code') == 200:
        cibData = uploadFile.get('returnObject')
        # 只取外幣金額不為NULL的
        cibData = cibData.filter(foreign_currency_amount__isnull=False)
        # 取定期存款外幣金額不為NULL的
        depositDataInCIBpage = depositData.filter(foreign_currency_amount__isnull=False)
        # 取得匯率
        exchangeRate = Exchangerate.objects.filter(rpt_id=rpt_id)
        rateDict = {}
        for exchangerate in exchangeRate:
            rateDict[exchangerate.currency_name] = exchangerate.rate
        # 計算核算金額、差異
        cibCalculatedAmountList = []
        cibDifferenceList = []
        cibRateList = []
        for cib in cibData:
            rate = rateDict.get(cib.currency)
            cibRateList.append(rate)
            calculatedAmount = rate * cib.foreign_currency_amount
            cibCalculatedAmountList.append(calculatedAmount)
            cibDifferenceList.append(calculatedAmount - cib.ntd_amount)
        zipForCib = zip(cibData, cibRateList, cibCalculatedAmountList, cibDifferenceList)

        depAccCalculatedAmountList = []
        depAccDifferenceList = []
        depAccRateList = []
        for depAcc in depositDataInCIBpage:
            rate = rateDict.get(depAcc.currency)
            depAccRateList.append(rate)
            calculatedAmount = rate * depAcc.foreign_currency_amount
            depAccCalculatedAmountList.append(calculatedAmount)
            depAccDifferenceList.append(calculatedAmount - depAcc.ntd_amount)
        zipForDepAcc = zip(depositDataInCIBpage, depAccRateList, depAccCalculatedAmountList, depAccDifferenceList)
    else:
        msg = uploadFile.get('msg')
        return render(request, 'adjust_page.html', {'comp_id': comp_id, 'rpt_id': rpt_id, 'acc_id': acc_id, 'msg': msg})

    # 取得分錄(acc_name, amount, adj_num, credit_debit)
    entries = Adjentry.objects.filter(front_end_location=2).select_related('pre__acc').filter(
        pre__rpt_id=rpt_id).values('pre__acc__acc_name',
                                   'amount', 'adj_num',
                                   'credit_debit',
                                   'entry_name',
                                   'front_end_location')

    entryList = []
    cibEntryList = []
    cibTotalEntryAmountList = []
    cibTotalAmount = 0
    # 先check是否有分錄
    if len(entries) != 0:
        adjNum = entries[0].get('adj_num')
        for entry in entries:
            # 計算調整總額
            # 用contains的方法判斷
            if (entry.get('pre__acc__acc_name') in entry.get('entry_name')):
                # 此分頁的分錄若計在借方都為正，計在貸方都為負
                if entry.get('credit_debit') == 0:
                    amount = entry.get('amount')
                else:
                    amount = -1 * entry.get('amount')
                cibTotalEntryAmountList.append([entry.get('pre__acc__acc_name'), amount])
                cibTotalAmount += amount
            # 同一組就丟進entryList
            if entry.get('adj_num') == adjNum:
                entryList.append(entry)
            # 出現新的adj_num
            else:
                # 先把上一組的entryList丟進cibEntryList
                cibEntryList.append(entryList)
                # 清空entryList
                entryList = []
                entryList.append(entry)
                adjNum = entry.get('adj_num')
        # 把最後一組的entryList丟進cibEntryList
        cibEntryList.append(entryList)
        # 差異合計
        if len(cibTotalEntryAmountList) != 0:
            cibTotalEntryAmountList.append(['合計數', cibTotalAmount])

    ############### 單一科目 - 調整頁面 的最後一個：查詢明細資料表和科目調整總表
    # 使用 rpt_id 和 acc_id 查詢 preamt_qry_set: book_amt 非 0 的，科目直接或間接是 acc_id 的子類別的，acc_id 為 23，24，25，26 的
    preamt_qry_set = Preamt.objects.filter((Q(rpt__rpt_id=rpt_id) & (
            Q(acc__acc_parent__acc_parent_id=acc_id) | Q(acc__acc_parent__acc_id=acc_id) | Q(
        acc__acc_id=acc_id) | Q(acc__acc_id__in=[23, 24, 25, 26])))).values('pre_id', 'acc__acc_name', 'book_amt',
                                                                            'adj_amt', 'pre_amt').order_by('pre_id')
    # print('preamt_qry_set >>> ', preamt_qry_set)
    # 得到查詢到的 preamt 的所有 pre_id
    preamt_id_list = list(preamt_qry_set.values_list('pre_id', flat=True))
    # print('preamt_id_list >>> ', preamt_id_list)
    # 使用 pre_id_list 查詢所有符合的 adj_entries_qry_set
    adj_entries_qry_set = Adjentry.objects.filter(pre__pre_id__in=preamt_id_list).values('adj_id', 'pre__acc__acc_name',
                                                                                         'credit_debit', 'amount',
                                                                                         'entry_name',
                                                                                         'adj_num').order_by('adj_num')
    # print('調整分錄配對之前的 qry set, adj_entries_qry_set >>> ', adj_entries_qry_set)
    # 處理調整分錄的配對：[{'credit': [cre_1, cre_2] , 'debit': [debit1, debit2]}, {其他相同的 adj_num 借貸配對}, ...]
    adj_num_list = list(adj_entries_qry_set.values_list('adj_num', flat=True).distinct())  # 共有幾個不同的 adj_num
    # print('adj_num_list >>> ', adj_num_list)
    adj_entries_list = []

    def filter_set(entry_list, adj_num, credit_debit):
        def iterator_func(item):
            # print('item >>> ', item)
            if item['adj_num'] == adj_num:
                if bool(item['credit_debit']) == bool(credit_debit):
                    return True
            return False

        return filter(iterator_func, entry_list)

    for adj_num in adj_num_list:
        adj_entries_list.append({'credit': list(filter_set(list(adj_entries_qry_set), adj_num, 0)),
                                 'debit': list(filter_set(list(adj_entries_qry_set), adj_num, 1))})
    # print('調整分錄配對好後的 list, adj_entries_list >>> ', adj_entries_list)
    return render(request, 'adjust_page.html',
                  {'comp_id': comp_id, 'rpt_id': rpt_id, 'acc_id': acc_id, 'preamts': preamt_qry_set,
                   'adj_entries': adj_entries_list,
                   'depositData': depositData, 'cibData': zipForCib, 'depositDataInCIB': zipForDepAcc,
                   'depositEntryList': depositEntryList,
                   'cibEntryList': cibEntryList, 'depositTotalEntryAmountList': depositTotalEntryAmountList,
                   'cibTotalEntryAmountList': cibTotalEntryAmountList})


@csrf_exempt
def new_report(request, comp_id):
    # 創造一個新的report
    # 取得起始與結束日期
    start_date = request.GET["start_date"]
    print(start_date)
    end_date = request.GET["end_date"]
    print(end_date)
    # 製造report
    Report.objects.create(start_date=start_date, end_date=end_date, com=Company.objects.get(com_id=comp_id), type="個體")
    # 查詢新增的report
    reports = Report.objects.filter(start_date=start_date, end_date=end_date, com=Company.objects.get(com_id=comp_id))
    for report in reports:
        new_report = report
    if new_report:
        rpt_id = new_report.rpt_id
    else:
        pass
    # 導到匯入頁
    acc_id = 1
    redirect_url = 'projects/%s/accounts/1/import' % (rpt_id)
    return redirect(redirect_url)


@csrf_exempt
def get_dashboard_page(request, comp_id):
    # 撈出公司的所有個體報表(datasource for 合併報表modal #1選擇報表)
    # Note: 如果採用點擊「合併報表」icon後才送ajax回傳html寫入modal，會造成無法設定click event給td -> 一載入dashboard就先去撈該公司所有的個體報表，把data塞進modal
    reports_to_combine = Report.objects.filter(com_id=comp_id, type='個體')
    # 暫時寫死為沒給的東西都是1，讓頁面其他按鈕有效果
    # 可修正為拿除dashboard頁上的navbar東西，就不需要這些
    return render(request, 'dashboard_page.html', {'comp_id': comp_id, 'reports_to_combine': reports_to_combine})


@csrf_exempt
def get_disclosure_page(request, comp_id, rpt_id, acc_id):
    """
    如果 method 是 GET，回傳正確 disclosure 頁面
    如果 method 是 POST，將傳回的 disclosure 檢查後存進資料庫
    """
    # 確認銀行存款和定期存款有被上傳
    if request.method == 'GET':
        table_name = 'cash_in_banks'
        uploadFile = get_uploaded_file(rpt_id, table_name)
        if uploadFile.get('status_code') == 200:
            table_name = 'deposit_account'
            uploadFile = get_uploaded_file(rpt_id, table_name)
            cibData = uploadFile.get('returnObject')
            # 成功被上傳，找出需回傳的 disdetail 和 disclosure (排除金額為0的)
            if uploadFile.get('status_code') == 200:
                depositData = uploadFile.get('returnObject')
                disname = Account.objects.filter(acc_id=acc_id).values('acc_name')
                disdetail_qry_set = Disdetail.objects.select_related('rpt__distitle__disdetail'). \
                    filter(dis_title__rpt_id=rpt_id, dis_title__dis_name=disname[0]['acc_name'], version_num=1). \
                    exclude(row_amt=0). \
                    values()
                disclosure_qry_set = Disclosure.objects.select_related('dis_title__rpt__pre__disclosure'). \
                    filter(pre__rpt_id=rpt_id, dis_detail__dis_title__dis_name=disname[0]['acc_name'], version_num=1). \
                    exclude(pre_amt=0). \
                    values('disclosure_id', 'pre_amt',
                           'pre__acc__acc_name',
                           'dis_detail__dis_detail_id')
                # 從未被對到的 disdetail 中選出 (disclosure - disdetail) 個。
                unspecified_disdetail_qry_set = Disdetail.objects.select_related('rpt__distitle__disdetail'). \
                                                    filter(dis_title__rpt__rpt_id=rpt_id, row_amt=0, version_num=1)[
                                                :(disclosure_qry_set.count() - disdetail_qry_set.count())].values()
                # print('unspecified_disdetail_qry_set >>> ', unspecified_disdetail_qry_set)

                # 找出需回傳階層表
                # 1. 找出 Level 2 科目，和其 Level 1 子科目
                # 2. Level 1 子科目找出對應的 disclosure
                # 3. 組成 disdetail_editor
                disdetail_editor = []
                level_1_disclosure_list = []
                level_2_account = Account.objects.filter(acc_parent=acc_id)
                for account_l2 in level_2_account:
                    level_1_account = Account.objects.filter(acc_parent=account_l2.acc_id)
                    for account_l1 in level_1_account:
                        if account_l1 is not None:
                            level_1_disclosure = Disclosure.objects.filter(pre__acc__acc_id=account_l1.acc_id,
                                                                           pre__rpt_id=rpt_id, version_num=1).exclude(pre_amt=0)
                        for disclosure in level_1_disclosure:
                            level_1_disclosure_list.append(disclosure.disclosure_id)
                            # print('level_1_disclosure_list:', level_1_disclosure_list)
                        else:
                            pass
                    if not level_1_disclosure_list:
                        pass
                    else:
                        disdetail_editor.append({
                            'acc_parent_name': account_l2.acc_name,
                            'disclosure_id_list': level_1_disclosure_list
                        })
                        level_1_disclosure_list = []
                print('disdetail_qry_set:', disdetail_qry_set)
                print('disclosure_qry_set:', disclosure_qry_set)
                # print('disdetail_editor:', disdetail_editor)
            else:
                msg = uploadFile.get('msg')
                return render(request, 'disclosure_page.html',
                              {'comp_id': comp_id, 'rpt_id': rpt_id, 'acc_id': acc_id, 'msg': msg})
        else:
            msg = uploadFile.get('msg')
            return render(request, 'disclosure_page.html',
                          {'comp_id': comp_id, 'rpt_id': rpt_id, 'acc_id': acc_id, 'msg': msg})
        return render(request, 'disclosure_page.html',
                      {'comp_id': comp_id, 'rpt_id': rpt_id, 'acc_id': acc_id, 'disdetail_qry_set': disdetail_qry_set,
                       'disclosure_qry_set': disclosure_qry_set, 'disdetail_editor': disdetail_editor,
                       'unspecified_disdetail_qry_set': unspecified_disdetail_qry_set})

    if request.method == 'POST' and request.is_ajax():
        data = json.loads(request.body)
        # print('傳的 data:', data)
        # TODO 檢查1: 有沒有重複的 dis_id (比對disclosure_list，有重複的就拿掉)
        # TODO 檢查2: 每個 disclosure 都要對到 disdetail (disclosure 數量)
        print(">>>data:", data)
        try:
            for disdetail_obj in data:
                # 更新 disclosure 所關聯的 disdetail
                disclosures = disdetail_obj['disclosures']
                total_pre_amt = 0
                for disclosure in disclosures:
                    a = Disclosure.objects.filter(disclosure_id=disclosure['disclosure_id'], version_num=1)
                    a.update(dis_detail_id=disdetail_obj['disdetail_id'])
                    total_pre_amt += a[0].pre_amt
                # 更新 disdetail row_name，並根據 pre_amt 總和更新 row_amt
                Disdetail.objects.filter(dis_detail_id=disdetail_obj['disdetail_id'], version_num=1) \
                    .update(row_name=disdetail_obj['row_name'], row_amt=total_pre_amt)
            # 更新附註格式時要把過去為了呈現前期比較而新增的Disdetail/Disclosure刪掉
            delete_disdetail_from_previous_comparison(rpt_id, acc_id)
            return JsonResponse({"status_code": 200, "msg": "成功更新附註格式。"})
        except Exception as e:
            print('update_disclosure exception >>> ', e)
            # return HttpResponseRedirect('{"status_code": 500, "msg": "發生不明錯誤。"}')
            return JsonResponse({"status_code": 500, "msg": "發生不明錯誤。"})


def consolidated_report(request, comp_id):
    comp_id = request.GET['comp_id']
    report_dates = request.GET['report_dates']
    temp_dates = report_dates.replace('年', '/').replace('月', '/').replace('日', '').replace('<span>', '').replace(
        '</span>', '')
    start_date = temp_dates[:temp_dates.find('~')]
    end_date = temp_dates[temp_dates.find('~') + 1:]

    # 取得欲合併報表期間的所有報表(母/子公司) (datasource for 合併報表modal #2簽名狀態)
    if request.GET['type'] == 'get_reports_with_status':
        print('modal #2')
        reports = Report.objects.raw('''
                                        WITH RECURSIVE cte_report AS (
                                            -- anchor
                                            SELECT c.com_name, r.*
                                            FROM Report AS r
                                            INNER JOIN Company AS c on r.com_id = c.com_id
                                            WHERE r.com_id = ''' + str(
            comp_id) + ' AND r.start_date = \'' + start_date + '\' AND r.end_date = \'' + end_date + '\' AND type = \'個體\''
                                     + '''UNION ALL
                                            -- recursive
                                            SELECT c.com_name, r.*
                                            FROM Report AS r
                                            INNER JOIN Company AS c on r.com_id = c.com_id
                                            INNER JOIN cte_report cr on c.com_parent = cr.com_id
                                            WHERE r.start_date = \'''' + start_date + '\' AND r.end_date = \'' + end_date + '\''
                                     + ''')
                                        SELECT * FROM cte_report;
                                    ''')
        tdStr1 = '<tr id="report_data"><td><span>company</span></td>'
        tdStr2 = '<td><span>已簽名</span></td>'
        tdStr3 = '<td><span>未簽名</span></td></tr>'
        returnStr = ''
        for report in reports:
            returnStr += tdStr1.replace('company', report.com_name)
            if report.signer != 0:
                returnStr += tdStr2
            else:
                returnStr += tdStr3
    # 點擊合併button後確認是否須建立合併Report/Preamt，導至consolidated_statement_page
    if request.GET['type'] == 'consolidate_report':
        # 前端傳回來的日期格式是'YYYY/MM/DD'，但query裡的日期格式必須是'YYYY-MM-DD'
        start_date = start_date.replace('/', '-')
        end_date = end_date.replace('/', '-')
        consolidate_rpt = Report.objects.filter(com_id=comp_id, type='合併', start_date=start_date, end_date=end_date)
        if len(consolidate_rpt) == 0:
            print('no consolidated report yet!!!! Now new create!')
            rpt_id = create_consolidated_report(comp_id, start_date, end_date)
            create_consolidated_report_preamt(rpt_id, comp_id, start_date, end_date)
            returnStr = 'projects/' + str(rpt_id) + '/'
        else:
            returnStr = 'projects/' + str(
                consolidate_rpt[0].rpt_id) + '/'  # 回傳url會有error，暫時用替換url的方式(dashboard_page -> projects/rpt_id)
    return JsonResponse({'returnStr': returnStr})


def get_consolidated_statement_page(request, comp_id, rpt_id):
    def check_null_or_not(i, amt):
        if not i:
            i = 0
        else:
            i = i.values()[0][amt]
        return i
    def check_null_or_not_for_target(i,target_id):
        if not i:
            i = 0
        else:
            i = i.values()[0][target_id]
        return i
    def set_total_adj_amt(list,total_adj_amt):
        a = 0
        while a < len(list):
            j = a + 1
            while j < len(list):
                if list[a]['com'] == list[j]['target'] and list[a]['amt'] ==-list[j]['amt']:
                    total_adj_amt=total_adj_amt+(-abs(list[a]['amt']))
                    del list[j]
                    del list[a]
                else:
                    j += 1
            a += 1
        return total_adj_amt
    def set_reltrx_list(dict,com,target,adj_amt,list):
            dict['com'] =com
            dict['target']= target
            dict['amt']= adj_amt
            if dict['target']!=0:
                list.append(dict)
            print(list,'list')

    # 撈日期
    start_date = Report.objects.filter(rpt_id=rpt_id).values()[0]['start_date']
    end_date = Report.objects.filter(rpt_id=rpt_id).values()[0]['end_date']
    # 此處rpt_id是合併報表的
    company_list = []
    demand_deposit_list = []  # 活期存款
    check_deposit_list = []  # 支票存款
    foreign_currency_deposit_list = []  # 外匯存款
    currency_cd_list = []  # 原幣定存
    foreign_currency_cd_list = []  # 外幣定存
    total_book_amt_demand_deposit = 0  # 活期存款book_amt
    total_book_amt_check_deposit = 0  # 支票存款book_amt
    total_book_amt_foreign_currency_deposit = 0  # 外匯存款book_amt
    total_book_amt_currency_cd = 0  # 原幣定存book_amt
    total_book_amt_foreign_currency_cd = 0  # 外幣定存book_amt
    total_adj_amt_demand_deposit = 0  # 活期存款adj_amt
    total_adj_amt_check_deposit = 0  # 支票存款adj_amt
    total_adj_amt_foreign_currency_deposit = 0  # 外匯存款adj_amt
    total_adj_amt_currency_cd = 0  # 原幣定存adj_amt
    total_adj_amt_foreign_currency_cd = 0  # 外幣定存adj_amts
    rel_demand_deposit_list=[]#合併沖銷 活期存款關係人交易list
    rel_check_deposit_list = []#合併沖銷 支票存款關係人交易list
    rel_foreign_currency_deposit_list = []#合併沖銷 外匯存款關係人交易list
    rel_currency_cd_list = []#合併沖銷 原幣定存關係人交易list
    rel_foreign_currency_cd_list = []#合併沖銷 外幣定存關係人交易list
    # 先撈舊報表的
    # 撈出母公司所屬的集團
    group_id = Company.objects.filter(com_id=comp_id).values()[0]['grp_id']
    # 撈出同個集團的所有公司
    com_list = Company.objects.filter(grp=group_id)
    # 撈出母公司幣別
    parent_currency = Company.objects.filter(com_id=comp_id).values()[0]['currency']
    # 撈出母公司rpt_id，以便在下方撈出匯率
    parent_rpt_id = \
        Report.objects.filter(com_id=comp_id).filter(start_date=start_date).filter(end_date=end_date).values()[0][
            'rpt_id']
    for i in com_list:
        # 查看該公司所使用的幣別
        currency = Company.objects.filter(com_id=i.com_id).values()[0]['currency']
        # 撈出該公司個體報表rpt_id(報表要是個體,且報表符合所選日期)
        report_id = \
            Report.objects.filter(com=i).filter(type='個體').filter(start_date=start_date).filter(
                end_date=end_date).values()[
                0]['rpt_id']
        # 撈活期存款 acc_id=11
        pre_amt_demand_deposit = Preamt.objects.filter(rpt=report_id).filter(acc=11)
        pre_amt_demand_deposit = check_null_or_not(pre_amt_demand_deposit, 'pre_amt')
        demand_deposit_list.append(pre_amt_demand_deposit)
        # 撈支票存款 acc_id=14
        pre_amt_check_deposit = Preamt.objects.filter(rpt=report_id).filter(acc=14)
        pre_amt_check_deposit = check_null_or_not(pre_amt_check_deposit, 'pre_amt')
        check_deposit_list.append(pre_amt_check_deposit)
        # 撈外匯存款 acc_id=17
        pre_amt_foreign_currency_deposit = Preamt.objects.filter(rpt=report_id).filter(acc=17)
        pre_amt_foreign_currency_deposit = check_null_or_not(pre_amt_foreign_currency_deposit, 'pre_amt')
        foreign_currency_deposit_list.append(pre_amt_foreign_currency_deposit)
        # 撈原幣定存 acc_id=21
        pre_amt_currency_cd = Preamt.objects.filter(rpt=report_id).filter(acc=21)
        pre_amt_currency_cd = check_null_or_not(pre_amt_currency_cd, 'pre_amt')
        currency_cd_list.append(pre_amt_currency_cd)
        # 撈外幣定存 acc_id=22
        pre_amt_foreign_currency_cd = Preamt.objects.filter(rpt=report_id).filter(acc=22)
        pre_amt_foreign_currency_cd = check_null_or_not(pre_amt_foreign_currency_cd, 'pre_amt')
        foreign_currency_cd_list.append(pre_amt_foreign_currency_cd)
        if currency == parent_currency:
            # 新增公司料表
            company_list.append(i.com_name + '(' + parent_currency + ')')
            # company_list.append(i)
            # 活期存款
            total_book_amt_demand_deposit = total_book_amt_demand_deposit + pre_amt_demand_deposit
            # 支票存款
            total_book_amt_check_deposit = total_book_amt_check_deposit + pre_amt_check_deposit
            # 外匯存款
            total_book_amt_foreign_currency_deposit = total_book_amt_foreign_currency_deposit + pre_amt_foreign_currency_deposit
            # 原幣定存
            total_book_amt_currency_cd = total_book_amt_currency_cd + pre_amt_currency_cd
            # 外幣定存
            total_book_amt_foreign_currency_cd = total_book_amt_foreign_currency_cd + pre_amt_foreign_currency_cd
        else:
            # 新增公司料表
            original_currency_company_name = i.com_name + '(' + currency + ')'
            company_list.append(original_currency_company_name)
            parrent_currency_company_name = i.com_name + '(' + parent_currency + ')'
            company_list.append(parrent_currency_company_name)
            #     company_list.append({'name':})
            # 撈出匯率
            exchange_rate = Exchangerate.objects.filter(currency_name=currency).filter(rpt=parent_rpt_id).values()[0][
                'rate']
            # 活期存款
            pre_amt_demand_deposit = pre_amt_demand_deposit * exchange_rate
            demand_deposit_list.append(pre_amt_demand_deposit)
            total_book_amt_demand_deposit = total_book_amt_demand_deposit + pre_amt_demand_deposit
            # 支票存款
            pre_amt_check_deposit = pre_amt_check_deposit * exchange_rate
            check_deposit_list.append(pre_amt_check_deposit)
            total_book_amt_check_deposit = total_book_amt_check_deposit + pre_amt_check_deposit
            # 外匯存款
            pre_amt_foreign_currency_deposit = pre_amt_foreign_currency_deposit * exchange_rate
            foreign_currency_deposit_list.append(pre_amt_foreign_currency_deposit)
            total_book_amt_foreign_currency_deposit = total_book_amt_foreign_currency_deposit + pre_amt_foreign_currency_deposit
            # 原幣定存
            pre_amt_currency_cd = pre_amt_currency_cd * exchange_rate
            currency_cd_list.append(pre_amt_currency_cd)
            total_book_amt_currency_cd = total_book_amt_currency_cd + pre_amt_currency_cd
            # 外幣定存
            pre_amt_foreign_currency_cd = pre_amt_foreign_currency_cd * exchange_rate
            foreign_currency_cd_list.append(pre_amt_foreign_currency_cd)
            total_book_amt_foreign_currency_cd = total_book_amt_foreign_currency_cd + pre_amt_foreign_currency_cd
        # 計算合併沖銷，撈出每間公司的關係人交易分錄
        # 先由每間公司對應的pre_amt_id，再撈出關係人交易，把關係人交易相加。
        # 撈活期存款pre_id acc_id=11
        print(">>> report_id:", report_id)
        pre_id_demand_deposit = Preamt.objects.filter(rpt=report_id).filter(acc=11).values()[0]['pre_id']
        # 再撈出關係人交易
        adj_amt_demand_deposit = Reltrx.objects.filter(pre=pre_id_demand_deposit)
        adj_amt_demand_deposit = check_null_or_not(adj_amt_demand_deposit, 'related_amt')
        target_demand_deposit = Reltrx.objects.filter(pre=pre_id_demand_deposit)
        target_demand_deposit = check_null_or_not_for_target(target_demand_deposit, 'target_id')
        adj_amt_demand_deposit_dict={}
        set_reltrx_list(adj_amt_demand_deposit_dict,i.com_id,target_demand_deposit,adj_amt_demand_deposit,rel_demand_deposit_list)
        # 撈支票存款pre_id acc_id=14
        pre_id_check_deposit = Preamt.objects.filter(rpt=report_id).filter(acc=14).values()[0]['pre_id']
        # 再撈出關係人交易
        adj_amt_check_deposit = Reltrx.objects.filter(pre=pre_id_check_deposit)
        adj_amt_check_deposit = check_null_or_not(adj_amt_check_deposit, 'related_amt')
        target_check_deposit = Reltrx.objects.filter(pre=pre_id_check_deposit)
        target_check_deposit = check_null_or_not_for_target(target_check_deposit, 'target_id')
        adj_amt_check_deposit_dict={}
        set_reltrx_list(adj_amt_check_deposit_dict,i.com_id,target_check_deposit,adj_amt_check_deposit,rel_check_deposit_list)
        # 撈外匯存款pre_id acc_id=17
        pre_id_foreign_currency_deposit = Preamt.objects.filter(rpt=report_id).filter(acc=17).values()[0]['pre_id']
        # 再撈出關係人交易
        adj_amt_foreign_currency_deposit = Reltrx.objects.filter(pre=pre_id_foreign_currency_deposit)
        adj_amt_foreign_currency_deposit = check_null_or_not(adj_amt_foreign_currency_deposit, 'related_amt')
        target_foreign_currency_deposit = Reltrx.objects.filter(pre=pre_id_foreign_currency_deposit)
        target_foreign_currency_deposit = check_null_or_not_for_target(target_foreign_currency_deposit, 'target_id')
        adj_amt_foreign_currency_deposit_dict={}
        set_reltrx_list(adj_amt_foreign_currency_deposit_dict,i.com_id,target_foreign_currency_deposit,adj_amt_foreign_currency_deposit,rel_foreign_currency_deposit_list)
        # 撈原幣定存pre_id acc_id=21
        pre_id_currency_cd = Preamt.objects.filter(rpt=report_id).filter(acc=21).values()[0]['pre_id']
        # 再撈出關係人交易
        adj_amt_currency_cd = Reltrx.objects.filter(pre=pre_id_currency_cd)
        adj_amt_currency_cd = check_null_or_not(adj_amt_currency_cd, 'related_amt')
        target_currency_cd = Reltrx.objects.filter(pre=pre_id_currency_cd)
        target_currency_cd = check_null_or_not_for_target(target_currency_cd, 'target_id')
        adj_amt_currency_cd_dict={}
        set_reltrx_list(adj_amt_currency_cd_dict,i.com_id,target_currency_cd,adj_amt_currency_cd,rel_currency_cd_list)
        # 撈外幣定存pre_id acc_id=22
        pre_id_foreign_currency_cd = Preamt.objects.filter(rpt=report_id).filter(acc=22).values()[0]['pre_id']
        # 再撈出關係人交易
        adj_amt_foreign_currency_cd = Reltrx.objects.filter(pre=pre_id_foreign_currency_cd)
        adj_amt_foreign_currency_cd = check_null_or_not(adj_amt_foreign_currency_cd, 'related_amt')
        target_foreign_currency_cd = Reltrx.objects.filter(pre=pre_id_foreign_currency_cd)
        target_foreign_currency_cd = check_null_or_not_for_target(target_foreign_currency_cd, 'target_id')
        adj_amt_foreign_currency_cd_dict={}
        set_reltrx_list(adj_amt_foreign_currency_cd_dict,i.com_id,target_foreign_currency_cd,adj_amt_foreign_currency_cd,rel_foreign_currency_cd_list)
    
    total_adj_amt_demand_deposit=set_total_adj_amt(rel_demand_deposit_list,total_adj_amt_demand_deposit)
    print('!',total_adj_amt_demand_deposit)
    total_adj_amt_check_deposit=set_total_adj_amt(rel_check_deposit_list,total_adj_amt_check_deposit)
    total_adj_amt_foreign_currency_deposit=set_total_adj_amt(rel_foreign_currency_deposit_list,total_adj_amt_foreign_currency_deposit)
    total_adj_amt_currency_cd=set_total_adj_amt(rel_currency_cd_list,total_adj_amt_currency_cd)
    total_adj_amt_foreign_currency_cd=set_total_adj_amt(rel_foreign_currency_cd_list,total_adj_amt_foreign_currency_cd)
    demand_deposit_list.append(total_book_amt_demand_deposit)
    demand_deposit_list.append(total_adj_amt_demand_deposit)
    demand_deposit_list.append(total_book_amt_demand_deposit + total_adj_amt_demand_deposit)
    check_deposit_list.append(total_book_amt_check_deposit)
    check_deposit_list.append(total_adj_amt_check_deposit)
    check_deposit_list.append(total_book_amt_check_deposit + total_adj_amt_check_deposit)
    foreign_currency_deposit_list.append(total_book_amt_foreign_currency_deposit)
    foreign_currency_deposit_list.append(total_adj_amt_foreign_currency_deposit)
    foreign_currency_deposit_list.append(
        total_book_amt_foreign_currency_deposit + total_adj_amt_foreign_currency_deposit)
    currency_cd_list.append(total_book_amt_currency_cd)
    currency_cd_list.append(total_adj_amt_currency_cd)
    currency_cd_list.append(total_book_amt_currency_cd + total_adj_amt_currency_cd)
    foreign_currency_cd_list.append(total_book_amt_foreign_currency_cd)
    foreign_currency_cd_list.append(total_adj_amt_foreign_currency_cd)
    foreign_currency_cd_list.append(total_book_amt_foreign_currency_cd + total_adj_amt_foreign_currency_cd)
    return render(request, 'consolidated_statement.html',
                  {'comp_id': comp_id, 'rpt_id': rpt_id, 'com_list': company_list,
                   'demand_deposit_list': demand_deposit_list,
                   'check_deposit_list': check_deposit_list,
                   'foreign_currency_deposit_list': foreign_currency_deposit_list,
                   'currency_cd_list': currency_cd_list, 'foreign_currency_cd_list': foreign_currency_cd_list,
                   'rel_demand_deposit_list':json.dumps(rel_demand_deposit_list),
                   'rel_check_deposit_list':json.dumps(rel_check_deposit_list),
                   'rel_foreign_currency_deposit_list':json.dumps(rel_foreign_currency_deposit_list),
                   'rel_currency_cd_list':json.dumps(rel_currency_cd_list),
                   'rel_foreign_currency_cd_list':json.dumps(rel_foreign_currency_cd_list),})


@csrf_exempt
def get_consolidated_disclosure_page(request, comp_id, rpt_id):
    # TODO 根據下拉式選單做改變
    # 因為round()的進位方式是「四捨六入五成雙」，跟一般的四捨五入不完全相同，故重新定義一個四捨五入的function
    def normal_round(amt):
        if amt / 1000 - math.floor(amt / 1000) < 0.5:
            return math.floor(amt / 1000)
        else:
            return math.ceil(amt / 1000)

    if request.is_ajax():
        # for合併報表更新附註格式
        if request.method == 'POST':
            print('hereeeeee')
            temp_data = json.loads(request.body)
            data = temp_data['result']
            acc_name = temp_data['acc_name']
            acc_id = Account.objects.get(acc_name=acc_name, acc_level=3).acc_id
            # print('傳的 data:', data)
            # TODO 檢查1: 有沒有重複的 dis_id (比對disclosure_list，有重複的就拿掉)
            # TODO 檢查2: 每個 disclosure 都要對到 disdetail (disclosure 數量)
            try:
                for disdetail_obj in data:
                    # 更新 disclosure 所關聯的 disdetail
                    disclosures = disdetail_obj['disclosures']
                    total_pre_amt = 0
                    for disclosure in disclosures:
                        a = Disclosure.objects.filter(disclosure_id=disclosure['disclosure_id'])
                        a.update(dis_detail_id=disdetail_obj['disdetail_id'])
                        total_pre_amt += a[0].pre_amt
                    # 更新 disdetail row_name，並根據 pre_amt 總和更新 row_amt
                    Disdetail.objects.filter(dis_detail_id=disdetail_obj['disdetail_id']) \
                        .update(row_name=disdetail_obj['row_name'], row_amt=total_pre_amt,
                                row_amt_in_thou=normal_round(total_pre_amt))  # 更新disdetail的同時也要更新row_amt_in_thou
                # 更新附註格式時要把過去為了呈現前期比較而新增的Disdetail/Disclosure刪掉
                delete_disdetail_from_previous_comparison(rpt_id, acc_id)
                return JsonResponse({"status_code": 200, "msg": "成功更新附註格式。"})
            except Exception as e:
                print('update_disclosure exception >>> ', e)
                # return HttpResponseRedirect('{"status_code": 500, "msg": "發生不明錯誤。"}')
                return JsonResponse({"status_codetotal_disdetail_in_thou": 500, "msg": "發生不明錯誤。"})
        # for合併報表附註格式設定頁的科目下拉選單
        else:
            print('in views via ajax nowwwwww')
            acc_name = request.GET['acc_name']
            print('acc_name >>>     ', acc_name)
            acc_id = Account.objects.get(acc_name=acc_name).acc_id
            print('acc_id >>>    ', acc_id)
            disname = Account.objects.filter(acc_id=acc_id).values('acc_name')
            disdetail_qry_set = Disdetail.objects.select_related('rpt__distitle__disdetail'). \
                filter(dis_title__rpt_id=rpt_id, dis_title__dis_name=disname[0]['acc_name'], version_num=1). \
                exclude(row_amt=0). \
                values()
            disclosure_qry_set = Disclosure.objects.select_related('dis_title__rpt__pre__disclosure'). \
                filter(pre__rpt_id=rpt_id, dis_detail__dis_title__dis_name=disname[0]['acc_name'], version_num=1). \
                exclude(pre_amt=0). \
                values('disclosure_id', 'pre_amt',
                       'pre__acc__acc_name',
                       'dis_detail__dis_detail_id')
            all_disdetail_qry_set = Disdetail.objects.select_related('rpt__distitle__disdetail'). \
                filter(dis_title__rpt__rpt_id=rpt_id, dis_title__dis_name=disname[0]['acc_name'], version_num=1).values()
            # 新增(disclosure - disdetail) 個disdetail備用
            diff_count = disclosure_qry_set.count() - disdetail_qry_set.count()
            print('all_disdetail_qry_set >>>     ', all_disdetail_qry_set)
            # 如果disdetail的數量比disclosure少，就新增差異數目的disdetail作為備用 # disclosure數量 - 有使用的disdetail數量
            if disclosure_qry_set.count() - all_disdetail_qry_set.count() != 0:  # disclosure數量 - 所有disdetail數量
                # 先取出report對應的distitle
                sb = '''
                       SELECT A.dis_title_id, A.dis_name
                       FROM Distitle A
                       INNER JOIN Account B ON A.dis_name = B.acc_name
                       WHERE A.rpt_id = ''' + str(rpt_id) + ' AND B.acc_id = ' + str(acc_id)
                distitle = Distitle.objects.raw(sb)[0]
                # print('distitle_id >>>>>>>>>', distitle.dis_title_id)
                # 新增(disclosure - disdetail)個 disdetail
                for i in range(diff_count):
                    Disdetail.objects.create(row_name='備用disdetail_' + str(i + 1), row_amt=0,
                                             dis_title=Distitle.objects.get(dis_title_id=distitle.dis_title_id))
            # 從未被對到的 disdetail 中選出 (disclosure - disdetail) 個。
            unspecified_disdetail_qry_set = Disdetail.objects.select_related('rpt__distitle__disdetail'). \
                                                filter(dis_title__rpt__rpt_id=rpt_id, row_amt=0, version_num=1)[
                                            :(disclosure_qry_set.count() - disdetail_qry_set.count())].values()
            print('unspecified_disdetail_qry_set >>> ', unspecified_disdetail_qry_set)

            # 找出需回傳階層表
            # 1. 找出 Level 2 科目，和其 Level 1 子科目
            # 2. Level 1 子科目找出對應的 disclosure
            # 3. 組成 disdetail_editor
            disdetail_editor = []
            level_1_disclosure_list = []
            level_2_account = Account.objects.filter(acc_parent=acc_id)
            for account_l2 in level_2_account:
                level_1_account = Account.objects.filter(acc_parent=account_l2.acc_id)
                for account_l1 in level_1_account:
                    if account_l1 is not None:
                        level_1_disclosure = Disclosure.objects.filter(pre__acc__acc_id=account_l1.acc_id,
                                                                       pre__rpt_id=rpt_id, version_num=1).exclude(pre_amt=0)
                    for disclosure in level_1_disclosure:
                        level_1_disclosure_list.append(disclosure.disclosure_id)
                        # print('level_1_disclosure_list:', level_1_disclosure_list)
                    else:
                        pass
                if not level_1_disclosure_list:
                    pass
                else:
                    disdetail_editor.append({
                        'acc_parent_name': account_l2.acc_name,
                        'disclosure_id_list': level_1_disclosure_list
                    })
                    level_1_disclosure_list = []

            disdetail_qry_set = list(disdetail_qry_set)
            disclosure_qry_set = list(disclosure_qry_set)
            unspecified_disdetail_qry_set = list(unspecified_disdetail_qry_set)
            return JsonResponse(
                {'comp_id': comp_id, 'rpt_id': rpt_id, 'acc_id': acc_id, 'disdetail_qry_set': disdetail_qry_set,
                 'disclosure_qry_set': disclosure_qry_set, 'disdetail_editor': disdetail_editor,
                 'unspecified_disdetail_qry_set': unspecified_disdetail_qry_set})
    # method == GET
    else:
        # Default進來會顯示現金及約當現金的附註格式
        acc_name = "現金及約當現金"
        print('acc_name >>>   ', acc_name)
        acc_id = Account.objects.get(acc_name=acc_name, acc_level=3).acc_id
        print('acc_id >>>  ', acc_id)
        print('rpt_id >>>  ', rpt_id)
        disname = Account.objects.filter(acc_id=acc_id).values('acc_name')
        print('disname >>>  ', disname)
        disdetail_qry_set = Disdetail.objects.select_related('rpt__distitle__disdetail'). \
            filter(dis_title__rpt_id=rpt_id, dis_title__dis_name=disname[0]['acc_name'], version_num=1). \
            exclude(row_amt=0). \
            values()
        print('-'*50)
        for i in disdetail_qry_set:
            print(i)
        print('-'*50)
        disclosure_qry_set = Disclosure.objects.select_related('dis_title__rpt__pre__disclosure'). \
            filter(pre__rpt_id=rpt_id, dis_detail__dis_title__dis_name=disname[0]['acc_name'], version_num=1). \
            exclude(pre_amt=0). \
            values('disclosure_id', 'pre_amt',
                   'pre__acc__acc_name',
                   'dis_detail__dis_detail_id')
        all_disdetail_qry_set = Disdetail.objects.select_related('rpt__distitle__disdetail'). \
            filter(dis_title__rpt__rpt_id=rpt_id, dis_title__dis_name=disname[0]['acc_name'], version_num=1).values()
        # 新增(disclosure - disdetail) 個disdetail備用
        diff_count = disclosure_qry_set.count() - disdetail_qry_set.count()  # disclosure數量 - 有使用的disdetail數量
        # print('diff_count >>>     ', diff_count)
        # 如果disdetail的數量比disclosure少，就新增差異數目的disdetail作為備用
        if disclosure_qry_set.count() - all_disdetail_qry_set.count() != 0:  # disclosure數量 - 所有disdetail數量
            # 先取出report對應的distitle
            sb = '''
                   SELECT A.dis_title_id, A.dis_name
                   FROM Distitle A
                   INNER JOIN Account B ON A.dis_name = B.acc_name
                   WHERE A.rpt_id = ''' + str(rpt_id) + ' AND B.acc_id = ' + str(acc_id)
            distitle = Distitle.objects.raw(sb)[0]
            # print('distitle_id >>>>>>>>>', distitle.dis_title_id)
            # 新增(disclosure - disdetail)個 disdetail
            for i in range(diff_count):
                Disdetail.objects.create(row_name='備用disdetail_' + str(i + 1), row_amt=0,
                                         dis_title=Distitle.objects.get(dis_title_id=distitle.dis_title_id))
        # 從未被對到的 disdetail 中選出 (disclosure - disdetail) 個。
        unspecified_disdetail_qry_set = Disdetail.objects.select_related('rpt__distitle__disdetail'). \
                                            filter(dis_title__rpt__rpt_id=rpt_id, row_amt=0, version_num=1)[
                                        :(disclosure_qry_set.count() - disdetail_qry_set.count())].values()
        print('unspecified_disdetail_qry_set >>> ', unspecified_disdetail_qry_set)

        # 找出需回傳階層表
        # 1. 找出 Level 2 科目，和其 Level 1 子科目
        # 2. Level 1 子科目找出對應的 disclosure
        # 3. 組成 disdetail_editor
        disdetail_editor = []
        level_1_disclosure_list = []
        level_2_account = Account.objects.filter(acc_parent=acc_id)
        for account_l2 in level_2_account:
            level_1_account = Account.objects.filter(acc_parent=account_l2.acc_id)
            for account_l1 in level_1_account:
                if account_l1 is not None:
                    level_1_disclosure = Disclosure.objects.filter(pre__acc__acc_id=account_l1.acc_id,
                                                                   pre__rpt_id=rpt_id, version_num=1).exclude(pre_amt=0)
                for disclosure in level_1_disclosure:
                    level_1_disclosure_list.append(disclosure.disclosure_id)
                    # print('level_1_disclosure_list:', level_1_disclosure_list)
                else:
                    pass
            if not level_1_disclosure_list:
                pass
            else:
                disdetail_editor.append({
                    'acc_parent_name': account_l2.acc_name,
                    'disclosure_id_list': level_1_disclosure_list
                })
                level_1_disclosure_list = []
        print('disdetail_qry_set:', disdetail_qry_set)
        print('disclosure_qry_set:', disclosure_qry_set)
        print('disdetail_editor:', disdetail_editor)
        return render(request, 'consolidated_disclosure_page.html',
                      {'comp_id': comp_id, 'rpt_id': rpt_id, 'acc_id': acc_id, 'disdetail_qry_set': disdetail_qry_set,
                       'disclosure_qry_set': disclosure_qry_set, 'disdetail_editor': disdetail_editor,
                       'unspecified_disdetail_qry_set': unspecified_disdetail_qry_set})


@csrf_exempt
def compare_with_last_consolidated_statement(request, comp_id, rpt_id):
    rpt_type = '合併'
    if request.method == 'GET':
        acc_id = 1 # Default進來會顯示現金及約當現金的附註格式
        ### 檢查是否已經有前期比較（version 2），若有則回傳前期比較。
        # 呼叫 search_previous_comparision
        current_disdetails_ver2, previous_disdetails_ver2 = search_previous_comparision(rpt_id, acc_id, rpt_type, comp_id)
        if current_disdetails_ver2 and previous_disdetails_ver2:  # 資料庫中有前期比較資料，則直接回傳
            print('data in DB')
            print('current >>> ', current_disdetails_ver2)
            print('previous >>> ', previous_disdetails_ver2)
            return render(request, 'consolidated_statement_compare_with_last_one.html', {
                'comp_id': comp_id, 'rpt_id': rpt_id, 'acc_id': acc_id,
                'previous_comparison_exists': True,
                 "now": current_disdetails_ver2, "past": previous_disdetails_ver2
            })
        else:
            # 若還沒有前期比較，則傳回 previous_comparison_exists: False 提示使用者要選擇以哪一期為基準
            ## 改動附註格式時只會刪除當期因呈現前期比較而新增的Disdetail/Disclosure，會導致只刪掉version_num為2的
            ## -> 如果沒有完整的前期比較，就把兩期rpt下version_num為2或3的Disdetail都刪掉
            current_rpt, previous_rpt = get_current_and_previous_rpt(rpt_id, rpt_type, comp_id)
            delete_disdetail_from_previous_comparison(current_rpt.rpt_id, acc_id)
            delete_disdetail_from_previous_comparison(previous_rpt.rpt_id, acc_id)
            return render(request, 'consolidated_statement_compare_with_last_one.html', {
                'comp_id': comp_id, 'rpt_id': rpt_id, 'acc_id': acc_id,
                'previous_comparison_exists': False,
            })
    elif request.method == 'POST' and request.is_ajax():  # 使用者選擇「當期」或「前期」為主要格式
        data = json.loads(request.body)
        base_period = data['base_period']
        acc_name = data['acc_name']
        acc_id = Account.objects.get(acc_name=acc_name, acc_level=3).acc_id
        # TODO 若是資料庫中已有前期比較資料，則需要先刪除。
        current_disdetails_ver2, previous_disdetails_ver2 = cal_previous_comparision(base_period, rpt_id, acc_id, rpt_type, comp_id)
        print('after ajax..')
        return JsonResponse({"status_code": 200, "base_period": base_period, "now": serialize('json', current_disdetails_ver2), "past": serialize('json', previous_disdetails_ver2)})    

@csrf_exempt
def previous_comparison(request, comp_id, rpt_id, acc_id):
    '''前期比較'''
    rpt_type = '個體'
    current_rpt, previous_rpt = get_current_and_previous_rpt(rpt_id, rpt_type, comp_id)
    distitle = Distitle.objects.get(rpt_id=rpt_id, dis_name=Account.objects.get(acc_id=acc_id).acc_name).dis_name
    if request.method == 'GET':
        ### 檢查是否已經有前期比較（version 2），若有則回傳前期比較。
        # 呼叫 search_previous_comparision
        current_disdetails_ver2, previous_disdetails_ver2 = search_previous_comparision(rpt_id, acc_id, rpt_type, comp_id)
        if current_disdetails_ver2 and previous_disdetails_ver2:  # 資料庫中有前期比較資料，則直接回傳
            return render(request, 'disclosure_previous_comparison_page.html', {
                'comp_id': comp_id, 'rpt_id': rpt_id, 'acc_id': acc_id,
                'distitle': distitle,
                'previous_comparison_exists': True,
                 "now": current_disdetails_ver2, "past": previous_disdetails_ver2,
                 'now_end_date': str(current_rpt.end_date), 'past_end_date': str(previous_rpt.end_date)
            })
       # else:
        # TODO 之後看情況要不要留 delete，這裡只是為了防止有沒有刪乾淨的 version
        delete_disdetail_from_previous_comparison(current_rpt.rpt_id, acc_id)
        delete_disdetail_from_previous_comparison(previous_rpt.rpt_id, acc_id)
        current_disdetails_ver2, previous_disdetails_ver2 = cal_previous_comparision('past', rpt_id, acc_id, rpt_type, comp_id)
        return render(request, 'disclosure_previous_comparison_page.html', {
            'comp_id': comp_id, 'rpt_id': rpt_id, 'acc_id': acc_id,
            'previous_comparison_exists': True,
            'distitle': distitle,
             "now": current_disdetails_ver2, "past": previous_disdetails_ver2,
             'now_end_date': str(current_rpt.end_date), 'past_end_date': str(previous_rpt.end_date)
        })
    elif request.method == 'POST' and request.is_ajax():  # 使用者選擇「當期」或「前期」為主要格式
        data = json.loads(request.body)
        print('data', data)
        print('data type', type(data))
        if type(data) == list: # 代表不是要調整前期比較格式，而是調整尾差
            id_list = [item['id'] for item in data]
            update_disdetail = []
            disdetail_qry_set = Disdetail.objects.filter(dis_detail_id__in=id_list)
            for item in data:
                disdetail = disdetail_qry_set.get(dis_detail_id=item['id'])
                disdetail.row_amt_in_thou = item['row_amt_in_thou']
                update_disdetail.append(disdetail)
            # 一次將 row_amt_in_thou 更新到資料庫
            Disdetail.objects.bulk_update(update_disdetail, ['row_amt_in_thou'])
            return JsonResponse({"status_code": 200, "msg": "成功更新尾差。"})
        elif data['base_period'] is not None: # 代表使用者要調整前期比較格式
            base_period = data['base_period']
            acc_name = data['acc_name']
            acc_id = Account.objects.get(acc_name=acc_name, acc_level=3).acc_id
            # TODO （看之後要不要刪）若是資料庫中已有前期比較資料，則需要先刪除。
            delete_disdetail_from_previous_comparison(current_rpt.rpt_id, acc_id)
            delete_disdetail_from_previous_comparison(previous_rpt.rpt_id, acc_id)
            current_disdetails_ver2, previous_disdetails_ver2 = cal_previous_comparision(base_period, rpt_id, acc_id, rpt_type, comp_id)
            return JsonResponse({"status_code": 200, "base_period": base_period, "now": serialize('json', current_disdetails_ver2), "past": serialize('json', previous_disdetails_ver2)})    
           


