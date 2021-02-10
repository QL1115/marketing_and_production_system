from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from pandas._libs import json
from .utils.Entries import create_preamount_and_adjust_entries_for_project_account
from .utils.RawFiles import delete_uploaded_file, check_and_save_cash_in_banks, check_and_save_deposit_account, \
    get_uploaded_file
from .utils.Disclosure import delete_disclosure_for_project_account
from django.db import connection
from .models import Cashinbanks, Depositaccount, Adjentry, Preamt, Exchangerate, Report, Account, Disclosure, Disdetail, \
    Distitle
from .forms import CashinbanksForm, DepositAccountForm
import xlrd  # xlrd 方法參考：https://blog.csdn.net/wangweimic/article/details/87344803
from django.db.models import Q


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
    entries = Adjentry.objects.filter(front_end_location=1).select_related('pre__acc').values('pre__acc__acc_name',
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
        exchangeRate = Exchangerate.objects.filter(rpt_id=1)
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
    entries = Adjentry.objects.filter(front_end_location=2).select_related('pre__acc').values('pre__acc__acc_name',
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
    # 暫時寫死為沒給的東西都是1，讓頁面其他按鈕有效果
    # 可修正為拿除dashboard頁上的navbar東西，就不需要這些
    return render(request, 'dashboard_page.html', {"acc_id": 1, 'comp_id': comp_id, 'rpt_id': 1})

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
                disdetail_qry_set = Disdetail.objects.select_related('rpt__distitle__disdetail'). \
                    filter(dis_title__rpt__rpt_id=rpt_id).exclude(row_amt=0).values()
                # disclosure_qry_set = Disclosure.objects.select_related('rpt__pre__disclosure'). \
                #     filter(pre__rpt__rpt_id=rpt_id).exclude(pre_amt=0).values('disclosure_id', 'pre_amt',
                #                                                               'dis_detail__row_name')
                disclosure_qry_set = Disclosure.objects.select_related('rpt__pre__disclosure'). \
                    filter(pre__rpt__rpt_id=rpt_id).exclude(pre_amt=0).values('disclosure_id', 'pre_amt',
                                                                              'pre__acc__acc_name', 'dis_detail__dis_detail_id')

                """
                找出需回傳階層表
                1. 找出 Level 2 科目，和其 Level 1 子科目
                2. Level 1 子科目找出對應的 disclosure
                3. 組成 disdetail_editor
                """
                disdetail_editor = []
                level_1_disclosure_list = []
                level_2_account = Account.objects.filter(acc_parent=acc_id)
                for account_l2 in level_2_account:
                    level_1_account = Account.objects.filter(acc_parent=account_l2.acc_id)
                    for account_l1 in level_1_account:
                        if account_l1 is not None:
                            level_1_disclosure = Disclosure.objects.filter(pre__acc__acc_id=account_l1.acc_id,
                                                                           pre__rpt_id=rpt_id).exclude(pre_amt=0)
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
                print('disdetail_editor:', disdetail_editor)
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
                       'disclosure_qry_set': disclosure_qry_set, 'disdetail_editor': disdetail_editor})

    if request.method == 'POST' and request.is_ajax():
        data = json.loads(request.body)
        print('傳的 data', data)
        # TODO 檢查1: 有沒有重複的 dis_id (比對disclosure_list，有重複的就拿掉)
        # TODO 檢查2: 每個 disclosure 都要對到 disdetail (disclosure 數量)
        try:
            for disdetail_obj in data:
                # 更新 row_name
                Disdetail.objects.filter(disdetail_id=disdetail_obj.disdetail_id) \
                    .update(row_name=disdetail_obj.row_name)
                # 更新 pre_amt 和所關聯的 disdetail
                Disclosure.objects.filter(disclosure_id=disdetail_obj.disclosures.get('disclosure_id')) \
                    .update(dis_detail_id=disdetail_obj.disdetail_id,
                            pre_amt=disdetail_obj.disclosures.get('pre_amt'))
        except Exception as e:
            print('update_disclosure exception >>> ', e)
            # return HttpResponseRedirect('{"status_code": 500, "msg": "發生不明錯誤。"}')
            return {"status_code": 500, "msg": "發生不明錯誤。"}
