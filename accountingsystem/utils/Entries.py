import datetime

from ..models import Cashinbanks, Depositaccount, Report, Account, Systemcode, Exchangerate,Adjentry,Preamt, Company, Disdetail, Disclosure, Distitle
from django.db import connection
from dateutil.relativedelta import relativedelta
from django.db.models import Sum, Q
from .Disclosure import create_disclosure_for_project_account, fill_in_disclosure


def create_preamount_and_adjust_entries_for_project_account(comp_id: object, rpt_id: object, acc_id: object) -> object:
    print('>>> create_preamount_and_adjust_entries_for_project_account')
    #建立調整和附註格式
    create_preamount(comp_id, rpt_id, acc_id)
    #建立分錄
    create_adjust_entries(comp_id, rpt_id, acc_id) 

def create_preamount(comp_id, rpt_id, acc_id):
    print('>>> create_preamount')
    if acc_id==1:
        create_cash_preamount(rpt_id, acc_id)

def create_cash_preamount(rpt_id, acc_id):
    print('>>> create cash preamount')
    preamount_list = []  #用於建立 disdetail
    countIdList = []
    acc_id = 1
    countIdList.append(acc_id)
    for i in countIdList:
        childList = Account.objects.filter(acc_parent=i)
        for a in childList:
            if a.acc_id in countIdList:
                pass
            else:
                countIdList.append(a.acc_id)
                # 要接一個account object
    number23 = Preamt.objects.create(book_amt=0, adj_amt=0, pre_amt=0, rpt=Report.objects.get(rpt_id=rpt_id), acc=Account.objects.get(acc_id=23))
    number24 = Preamt.objects.create(book_amt=0, adj_amt=0, pre_amt=0, rpt=Report.objects.get(rpt_id=rpt_id), acc=Account.objects.get(acc_id=24))
    number25 = Preamt.objects.create(book_amt=0, adj_amt=0, pre_amt=0, rpt=Report.objects.get(rpt_id=rpt_id), acc=Account.objects.get(acc_id=25))
    number26 = Preamt.objects.create(book_amt=0, adj_amt=0, pre_amt=0, rpt=Report.objects.get(rpt_id=rpt_id), acc=Account.objects.get(acc_id=26))
    preamount_list.append(number23)
    preamount_list.append(number24)
    preamount_list.append(number25)
    preamount_list.append(number26)
    #print('>>> number23', number23[0].acc_id)
    #print('preamount_list >>>', preamount_list)

    for i in countIdList:
        preamount = Preamt.objects.create(book_amt=0, adj_amt=0, pre_amt=0, rpt=Report.objects.get(rpt_id=rpt_id), acc=Account.objects.get(acc_id=i))
        preamount_list.append(preamount)

    create_disclosure_for_project_account(preamount_list, rpt_id, acc_id)

def create_adjust_entries(comp_id, rpt_id, acc_id):
    #如果科目是現金，建立現金的分錄
    print('>>> create_adjust_entries')
    if acc_id==1:
        create_cash_adjust_entries(comp_id,rpt_id, acc_id)

def create_cash_adjust_entries(comp_id,rpt_id, acc_id):
    # 建立所有現金的 adjust entry
    print('>>> create_cash_adjust_entries')

    Depositaccount.objects.filter(rpt_id=rpt_id).update(already_adjust=0)

    cash_in_bank_qry_set=Cashinbanks.objects.filter(rpt_id=rpt_id).values()
    deposit_account_qry_set=Depositaccount.objects.filter(rpt_id=rpt_id).values()
    cash_qry_set={ 'cash_in_banks': cash_in_bank_qry_set,'deposit_account': deposit_account_qry_set}

    #定期存款-質押存款
    pledge_deposit = create_pledge_deposit_account_entry(comp_id,cash_qry_set,rpt_id)
    #定期存款-超過三個月定存
    over_3_month_dp = create_over_3_month_deposit_entry(comp_id,cash_qry_set, rpt_id)
    #銀行存款-外匯存款
    foreign_currency_deposit = create_foreign_currency_deposit_entry(comp_id,cash_qry_set,rpt_id)
    #銀行存款-外幣定存
    foreign_currency_time_deposit = create_foreign_currency_time_deposit(comp_id,cash_qry_set,rpt_id)
    #銀行存款-超過三個月定存
    cib_over_3_month = create_over_three_month_time_deposit(comp_id,cash_qry_set,rpt_id)
    #
    li = [over_3_month_dp, pledge_deposit, foreign_currency_deposit, foreign_currency_time_deposit, cib_over_3_month]
    fill_in_preamount(li, comp_id, rpt_id, acc_id)


# 銀行存款-外匯存款
def create_foreign_currency_deposit_entry(comp_id,cash_qry_set, rpt_id):
    print('>>> create_foreign_currency_deposit_entry')
    cash_in_banks = cash_qry_set['cash_in_banks']
    total_difference = 0
    exchangerate = 0
    for cash_in_bank in cash_in_banks:
        if cash_in_bank['currency'] != Company.objects.filter(com_id=comp_id)[0].currency:
            # exchangerate
            exchangerate = Exchangerate.objects.filter(currency_name=cash_in_bank['currency']).filter(rpt_id=rpt_id)[
                0].rate
            difference = (exchangerate * cash_in_bank['foreign_currency_amount']) - cash_in_bank['ntd_amount']
            total_difference = total_difference + difference
    # 撈出最大的adj_num
    bigest_adj_num = 0
    cursor1 = connection.cursor()
    cursor1.execute("select count(*) from Adjentry")
    aleady_entry = cursor1.fetchall()[0][0]
    if aleady_entry == 0:
        bigest_adj_num = 0
    else:
        bigest_adj_num = bigest_num = Adjentry.objects.latest('adj_num').adj_num
    # 撈出外匯存款preamt object
    foreign_curency_deposit＿pre_id = Preamt.objects.filter(rpt_id=rpt_id).filter(acc_id=17)[0]
    # 建立分路#借兌換損失貸外匯存款
    if total_difference < 0:
        # 撈出兌換損失pre object
        foreign_exchange_lost＿pre_id = Preamt.objects.filter(rpt_id=rpt_id).filter(acc_id=25)[0]
        # 寫入adjentry前，total_difference要先轉成正
        total = total_difference * -1
        # 寫入adjentry
        credit_foreign_exchange_losses = Adjentry.objects.create(amount=total, adj_num=bigest_adj_num + 1,
                                                                 pre=foreign_exchange_lost＿pre_id, credit_debit=0,
                                                                 front_end_location=2, entry_name='外幣評價損益_外匯存款')
        debit_foreign_currency_deposit = Adjentry.objects.create(amount=total, adj_num=bigest_adj_num + 1,
                                                                 pre=foreign_curency_deposit＿pre_id, credit_debit=1,
                                                                 front_end_location=2, entry_name='外幣評價損益_外匯存款')
        foreign_currency_deposit＿entry_list = {}
        foreign_currency_deposit＿entry_list = {'兌換損失': credit_foreign_exchange_losses,
                                               '外匯存款': debit_foreign_currency_deposit}
        return foreign_currency_deposit＿entry_list
    # 建立分路#借外匯存款貸兌換利益
    elif total_difference > 0:
        # 撈出兌換利益pre object
        foreign_exchange_gain＿pre_id = Preamt.objects.filter(rpt_id=rpt_id).filter(acc_id=26)[0]
        # 寫入adjentry
        credit_foreign_currency_deposit = Adjentry.objects.create(amount=total_difference, adj_num=bigest_adj_num + 1,
                                                                  pre=foreign_curency_deposit＿pre_id, credit_debit=0,
                                                                  front_end_location=2, entry_name='外幣評價損益_外匯存款')
        debit_foreign_exchange_gain = Adjentry.objects.create(amount=total_difference, adj_num=bigest_adj_num + 1,
                                                              pre=foreign_exchange_gain＿pre_id, credit_debit=1,
                                                              front_end_location=2, entry_name='外幣評價損益_外匯存款')
        foreign_currency_deposit＿entry_list = {}
        foreign_currency_deposit＿entry_list = {'兌換利益': debit_foreign_exchange_gain,
                                               '外匯存款': credit_foreign_currency_deposit}
        return foreign_currency_deposit＿entry_list


# 銀行存款-外幣定存
# 此method請放在定期存款調整後
def create_foreign_currency_time_deposit(comp_id,cash_qry_set, rpt_id):
    print('>>> create_foreign_currency_time_deposit')
    exchangerate = 0
    total_difference = 0
    # 重新撈定期存款，因為會需要查看有沒有調整
    deposit_accounts = Depositaccount.objects.all().values()
    for deposit_account in deposit_accounts:
        if deposit_account['currency'] != Company.objects.filter(com_id=comp_id)[0].currency and deposit_account['already_adjust'] != 1:
            # exchangerate
            exchangerate = Exchangerate.objects.filter(currency_name=deposit_account['currency']).filter(rpt_id=rpt_id)[
                0].rate
            difference = (exchangerate * deposit_account['foreign_currency_amount']) - deposit_account['ntd_amount']
            total_difference = total_difference + difference
    # 撈出最大的adj_num
    bigest_adj_num = 0
    cursor1 = connection.cursor()
    cursor1.execute("select count(*) from Adjentry")
    aleady_entry = cursor1.fetchall()[0][0]
    if aleady_entry == 0:
        bigest_adj_num = 0
    else:
        bigest_adj_num = bigest_num = Adjentry.objects.latest('adj_num').adj_num
    # 撈出外幣定存preamt object
    foreign_curency_time_deposit＿pre_id = Preamt.objects.filter(rpt_id=rpt_id).filter(acc_id=22)[0]
    # 建立分路#借兌換損失貸外匯存款
    if total_difference < 0:
        # 撈出兌換損失pre object
        foreign_exchange_lost＿pre_id = Preamt.objects.filter(rpt_id=rpt_id).filter(acc_id=25)[0]
        # 寫入adjentry前，total_difference要先轉成正
        total = total_difference * -1
        # 寫入adjentry
        credit_foreign_exchange_losses = Adjentry.objects.create(amount=total, adj_num=bigest_adj_num + 1,
                                                                 pre=foreign_exchange_lost＿pre_id, credit_debit=0,
                                                                 front_end_location=2, entry_name='外幣評價損益_外幣定存')
        debit_foreign_currency_time_deposit = Adjentry.objects.create(amount=total, adj_num=bigest_adj_num + 1,
                                                                      pre=foreign_curency_time_deposit＿pre_id,
                                                                      credit_debit=1, front_end_location=2,
                                                                      entry_name='外幣評價損益_外幣定存')
        foreign_currency_time_deposit_entry_list = {}
        foreign_currency_time_deposit_entry_list = {'兌換損失': credit_foreign_exchange_losses,
                                                    '外幣定存': debit_foreign_currency_time_deposit}
        return foreign_currency_time_deposit_entry_list
    # 建立分路#借外匯存款貸兌換利益
    elif total_difference > 0:
        # 撈出兌換利益pre object
        foreign_exchange_gain＿pre_id = Preamt.objects.filter(rpt_id=rpt_id).filter(acc_id=26)[0]
        # 寫入adjentry
        credit_foreign_currency_time_deposit = Adjentry.objects.create(amount=total_difference,
                                                                       adj_num=bigest_adj_num + 1,
                                                                       pre=foreign_curency_time_deposit＿pre_id,
                                                                       credit_debit=0, front_end_location=2,
                                                                       entry_name='外幣評價損益_外幣定存')
        debit_foreign_exchange_gain = Adjentry.objects.create(amount=total_difference, adj_num=bigest_adj_num + 1,
                                                              pre=foreign_exchange_gain＿pre_id, credit_debit=1,
                                                              front_end_location=2, entry_name='外幣評價損益_外幣定存')
        foreign_currency_time_deposit_entry_list = {}
        foreign_currency_time_deposit_entry_list = {'兌換利益': debit_foreign_exchange_gain,
                                                    '外幣定存': credit_foreign_currency_time_deposit}
        return foreign_currency_time_deposit_entry_list


# 銀行存款-超過三個月定存
def create_over_three_month_time_deposit(comp_id,cash_qry_set, rpt_id):
    print('>>> create_over_three_month_time_deposit')
    exchangerate = 0
    total_difference = 0
    # 重新撈定期存款，因為會需要查看有沒有調整
    deposit_accounts = Depositaccount.objects.filter(rpt_id=rpt_id).values()
    for deposit_account in deposit_accounts:
        if deposit_account['currency'] != Company.objects.filter(com_id=comp_id)[0].currency and deposit_account['already_adjust'] == 1 and deposit_account[
            'plege'] == 0:
            # exchangerate
            exchangerate = Exchangerate.objects.filter(currency_name=deposit_account['currency']).filter(rpt_id=rpt_id)[
                0].rate
            difference = (exchangerate * deposit_account['foreign_currency_amount']) - deposit_account['ntd_amount']
            total_difference = total_difference + difference
    # 撈出最大的adj_num
    bigest_adj_num = 0
    cursor1 = connection.cursor()
    cursor1.execute("select count(*) from Adjentry")
    aleady_entry = cursor1.fetchall()[0][0]
    if aleady_entry == 0:
        bigest_adj_num = 0
    else:
        bigest_adj_num = bigest_num = Adjentry.objects.latest('adj_num').adj_num
    # 撈出超過三個月定存preamt object
    over_three_month_time_deposit＿pre_id = Preamt.objects.filter(rpt_id=rpt_id).filter(acc_id=23)[0]
    if total_difference < 0:
        # 撈出兌換損失pre object
        foreign_exchange_lost＿pre_id = Preamt.objects.filter(rpt_id=rpt_id).filter(acc_id=25)[0]
        # 寫入adjentry前，total_difference要先轉成正
        total = total_difference * -1
        # 寫入adjentry
        credit_foreign_exchange_losses = Adjentry.objects.create(amount=total, adj_num=bigest_adj_num + 1,
                                                                 pre=foreign_exchange_lost＿pre_id, credit_debit=0,
                                                                 front_end_location=2, entry_name='外幣評價損益_超過三個月定存')
        debit_over_three_month_time_deposit = Adjentry.objects.create(amount=total, adj_num=bigest_adj_num + 1,
                                                                      pre=over_three_month_time_deposit＿pre_id,
                                                                      credit_debit=1, front_end_location=2,
                                                                      entry_name='外幣評價損益_超過三個月定存')
        over_three_month_time_deposit＿entry_list = {}
        over_three_month_time_deposit＿entry_list = {'超過三個月定存': debit_over_three_month_time_deposit,
                                                    '兌換損失': credit_foreign_exchange_losses}
        return over_three_month_time_deposit＿entry_list
    # 建立分路#借外匯存款貸兌換利益
    elif total_difference > 0:
        # 撈出兌換利益pre object
        foreign_exchange_gain＿pre_id = Preamt.objects.filter(rpt_id=rpt_id).filter(acc_id=26)[0]
        # 寫入adjentry
        credit_over_three_month_time_deposit = Adjentry.objects.create(amount=total_difference,
                                                                       adj_num=bigest_adj_num + 1,
                                                                       pre=over_three_month_time_deposit＿pre_id,
                                                                       credit_debit=0, front_end_location=2,
                                                                       entry_name='外幣評價損益_超過三個月定存')
        debit_foreign_exchange_gain = Adjentry.objects.create(amount=total_difference, adj_num=bigest_adj_num + 1,
                                                              pre=foreign_exchange_gain＿pre_id, credit_debit=1,
                                                              front_end_location=2, entry_name='外幣評價損益_超過三個月定存')
        over_three_month_time_deposit＿entry_list = {}
        over_three_month_time_deposit＿entry_list = {'超過三個月定存': credit_over_three_month_time_deposit,
                                                    '兌換利益': debit_foreign_exchange_gain}
        return over_three_month_time_deposit＿entry_list

#定期存款-超過三個月定存
def create_over_3_month_deposit_entry(comp_id,cash_qry_set, rpt_id):
    #建立超過三個月定存調整分錄
    print('>>> create_over_3_month_deposit_entry')
    ntd_total = 0
    foreign_currency_total = 0
    deposit_account = cash_qry_set['deposit_account']
    report_end_date = Report.objects.filter(rpt_id=rpt_id).values('end_date')
    report_end_year = report_end_date[0]['end_date'].year
    report_end_month = report_end_date[0]['end_date'].month
    #x=0

    #計算時間差(月)
    for deposit_account in deposit_account:
        deposit_year = deposit_account['end_date'].year
        deposit_month = deposit_account['end_date'].month
        duration = 12 * (deposit_year - report_end_year) + (deposit_month - report_end_month)
        if deposit_account['already_adjust'] != 1 and duration > 3:
           Depositaccount.objects.filter(rpt_id=rpt_id, dep_acc_id=deposit_account['dep_acc_id']).update(already_adjust=1)
           if deposit_account['foreign_currency_amount'] != None:
              foreign_currency_total += deposit_account['ntd_amount']
           else:
              ntd_total += deposit_account['ntd_amount']
        #x+=1
        #print(x, "foreign_currency_total:", foreign_currency_total, "ntd_total", ntd_total)

    '''撈出最大的adj_num(可以寫一個method)'''
    cursor1 = connection.cursor()
    cursor1.execute("select count(*) from Adjentry")
    aleady_entry=cursor1.fetchall()[0][0]
    if aleady_entry==0:
        bigest_adj_num=0
    else:
        bigest_adj_num=Adjentry.objects.latest('adj_num').adj_num

    #撈出 preamount id
    over_3_month_pre_id = Preamt.objects.filter(rpt_id=rpt_id).filter(acc_id=23)[0]
    ntd_deposit_pre_id = Preamt.objects.filter(rpt_id=rpt_id).filter(acc_id=21)[0]
    foreign_currency_pre_id = Preamt.objects.filter(rpt_id=rpt_id).filter(acc_id=22)[0]

    #create_adjust_entry for ntd_over_3_month_total
    credit_ntd_over_3_month_total = Adjentry.objects.create(amount=ntd_total+foreign_currency_total, adj_num=bigest_adj_num + 1,
                                                             pre=over_3_month_pre_id, credit_debit=0,
                                                             front_end_location=1, entry_name= '超過三個月定存')
    #create_adjust_entry for 台幣定存
    debit_ntd_deposit_total = Adjentry.objects.create(amount=ntd_total, adj_num=bigest_adj_num + 1,
                                                             pre=ntd_deposit_pre_id, credit_debit=1,
                                                             front_end_location=1, entry_name='超過三個月定存')

    #create_adjust_entry for 外幣定存
    debit_foreign_currency_deposit_total = Adjentry.objects.create(amount=foreign_currency_total, adj_num=bigest_adj_num + 1,
                                                             pre=foreign_currency_pre_id, credit_debit=1,
                                                             front_end_location=1, entry_name='超過三個月定存')

    return{"超過三個月定存": credit_ntd_over_3_month_total,
           "原幣定存": debit_ntd_deposit_total,
           "外幣定存": debit_foreign_currency_deposit_total}

#定期存款-質押存款
def create_pledge_deposit_account_entry(comp_id,cash_qry_set, rpt_id):
    print('>>> create_pledge_deposit_account_entry')
    plege_total = 0
    deposit_account = cash_qry_set['deposit_account']

    for deposit_account in deposit_account:
        if deposit_account['plege'] == 1:
            deposit_account['already_adjust'] = 1
            Depositaccount.objects.filter(rpt_id=rpt_id, dep_acc_id=deposit_account['dep_acc_id']).update(already_adjust=1)
            plege_total += deposit_account['ntd_amount']

    '''撈出最大的adj_num(可以寫一個method)'''
    cursor1 = connection.cursor()
    cursor1.execute("select count(*) from Adjentry")
    aleady_entry=cursor1.fetchall()[0][0]
    if aleady_entry==0:
        bigest_adj_num=0
    else:
        bigest_adj_num=Adjentry.objects.latest('adj_num').adj_num

    #撈出 preamount id
    plege_pre_id = Preamt.objects.filter(rpt_id=rpt_id).filter(acc_id=24)[0]
    ntd_deposit_pre_id = Preamt.objects.filter(rpt_id=rpt_id).filter(acc_id=21)[0]

    #create_adjust_entry_for_pledge
    #(amount, adj_num, pre_id, credit_debit, front_end_location)
    #(pledge_total, 目前最大(與上同), preamount.report_id = report_id 的 pre_id, 0, 1)
    credit_pledge_total = Adjentry.objects.create(amount=plege_total, adj_num=bigest_adj_num + 1,
                                                             pre=plege_pre_id, credit_debit=0,
                                                             front_end_location=1,entry_name='質押定存')
    #create_adjust_entry_for_台幣定存
    #(amount, adj_num, pre_id, credit_debit, front_end_location)
    #(pledge_total, 目前最大(與上同), preamount.report_id = report_id 的 pre_id, 1, 1)
    debit_ntd_deposit_total = Adjentry.objects.create(amount=plege_total, adj_num=bigest_adj_num + 1,
                                                             pre=ntd_deposit_pre_id, credit_debit=1,
                                                             front_end_location=1, entry_name='質押定存')
    return{"質押定存": credit_pledge_total,
           "原幣定存": debit_ntd_deposit_total}

def fill_in_preamount(list,  comp_id, rpt_id, acc_id):
    '''
    將 adjust entry 中計算完成的 preamount 塞回。
    :param list: eg. [{"質押定存": 質押定存obj, "台幣定存": 台幣定存obj}, {"外匯存款", 外匯存款obj}, {...}, ...]
    :return JSON format string，代表成功或失敗
    '''

    # if acc_id == 1: # TODO 待確定，這個科目到底是 「現金及約當現金(id: 1)」還是「現金(id: 4)」?
    print('>>> fill in preamount')
    #print('list >>> ', list)
    try:
        # 1. 撈 cashinbank 及 depositaccount 這兩個 table 內的 type，找出對應的 account id 後決定邏輯。
        cash_in_bank_qry_set = Cashinbanks.objects.filter(rpt__rpt_id=rpt_id)
        cashinbank_type_and_ntd_amount = cash_in_bank_qry_set.values('type__acc_id', 'type__acc_name').annotate(ntd_amount = Sum('ntd_amount'))
        # print('cashinbank.query >>> ', cashinbank_type_and_ntd_amount.query)
        # print('cashinbank_type_and_ntd_amount >>> ', cashinbank_type_and_ntd_amount)
        deposit_account_qry_set = Depositaccount.objects.filter(rpt__rpt_id=rpt_id)
        depositaccount_type_and_ntd_amount = deposit_account_qry_set.values('type__acc_id', 'type__acc_name').annotate(ntd_amount = Sum('ntd_amount'))
        # print('depositaccount.query >>> ', depositaccount_type_and_ntd_amount.query)
        # print('depositaccount_type_and_ntd_amount >>> ', depositaccount_type_and_ntd_amount)

        # 使用上傳資料表的 type 的 acc id 和 rpt_id 查出對應的 preamount qry set
        rpt_acc_tuples = tuple([(rpt_id, item['type__acc_id']) for item in cashinbank_type_and_ntd_amount.values('type__acc_id')]) + tuple([(rpt_id, item['type__acc_id']) for item in depositaccount_type_and_ntd_amount.values('type__acc_id')])
        # print('rpt_acc_tuples >>> ', rpt_acc_tuples)
        # 寫法參考：https://stackoverflow.com/a/41717889
        preamt_qry_set = Preamt.objects.extra(where=['(rpt_id, acc_id) in %s'], params=[rpt_acc_tuples])
        # print('preamt_qry_set >>> ', preamt_qry_set)

        # 各個不同 account 的邏輯
        # 目前 list 中 index，0: 超過三個月定存＿entry(), 1: 質押定存＿entry(), 2: 外匯存款＿entry(), 3: 外幣定存＿entry(), 4: 超過三個月定存匯率差_entry()
        # TODO 「活期存款」和「支票存款」目前沒有例子，故暫時不調。目前只調整「外幣存款」、「台幣定存」、「外幣定存」
        # adj_demand_deposit: 活期存款調整數, adj_check_deposit: 支票存款調整數, adj_foreign_currency_deposit: 外匯存款調整數, adj_exchange_loss: 兌換損失, adj_exchange_gain: 兌換利益
        # adj_foreign_currency_cd: 外幣定存調整數, adj_ntd_cd: 台幣定存調整數, adj_exceed_three_months_dp: 超過三個月定存, adj_pledge: 質押定存

        report_end_date = Report.objects.get(rpt_id=rpt_id).end_date
        # print('!!!!!!', report_end_date + relativedelta(months=3))
        # 報導結束日
        # 2. 設置 preamt value
        # 活期存款 preamt
        # print('cashinbank_type_and_ntd_amount.get(type__acc_name="活期存款").get("type__acc_id") >>> ', cashinbank_type_and_ntd_amount.get(type__acc_name='活期存款').get('type__acc_id'))
        preamt_demand_deposit = preamt_qry_set.get(acc__acc_id=cashinbank_type_and_ntd_amount.get(type__acc_name='活期存款').get('type__acc_id'))
        # print('活期存款 preamt >>> ', preamt_demand_deposit)
        preamt_demand_deposit.book_amt = cashinbank_type_and_ntd_amount.get(type__acc_name='活期存款').get('ntd_amount')
        preamt_demand_deposit.adj_amt = 0 # TODO
        preamt_demand_deposit.pre_amt = preamt_demand_deposit.book_amt + preamt_demand_deposit.adj_amt
        preamt_demand_deposit.save()
        # print('活期存款：{}, {}, {}'.format(preamt_demand_deposit.book_amt, preamt_demand_deposit.adj_amt, preamt_demand_deposit.pre_amt))

        # 支票存款 preamt
        preamt_check_deposit = preamt_qry_set.get(acc__acc_id=cashinbank_type_and_ntd_amount.get(type__acc_name='支票存款').get('type__acc_id'))
        # print('支票存款 preamt >>> ', preamt_check_deposit)
        preamt_check_deposit.book_amt = cashinbank_type_and_ntd_amount.get(type__acc_name='支票存款').get('ntd_amount')
        preamt_check_deposit.adj_amt = 0  # TODO
        preamt_check_deposit.pre_amt = preamt_check_deposit.book_amt + preamt_check_deposit.adj_amt
        preamt_check_deposit.save()
        # print('支票存款：{}, {}, {}'.format(preamt_check_deposit.book_amt, preamt_check_deposit.adj_amt, preamt_check_deposit.pre_amt))

        # 外匯存款 preamt
        preamt_foreign_currency_deposit = preamt_qry_set.get(acc__acc_id=cashinbank_type_and_ntd_amount.get(type__acc_name='外匯存款').get('type__acc_id'))
        # print('外匯存款 preamt >>> ', preamt_foreign_currency_deposit)
        preamt_foreign_currency_deposit.book_amt = cashinbank_type_and_ntd_amount.get(type__acc_name='外匯存款').get('ntd_amount')
        preamt_foreign_currency_deposit.adj_amt = list[2]['外匯存款'].amount if list[2]['外匯存款'].credit_debit == 0 else list[2]['外匯存款'].amount*(-1)
        preamt_foreign_currency_deposit.pre_amt = preamt_foreign_currency_deposit.book_amt + preamt_foreign_currency_deposit.adj_amt
        preamt_foreign_currency_deposit.save()
        # print('外匯存款：{}, {}, {}'.format(preamt_foreign_currency_deposit.book_amt, preamt_foreign_currency_deposit.adj_amt, preamt_foreign_currency_deposit.pre_amt))

        # 原幣定存 preamt
        currency = Company.objects.filter(com_id=comp_id).values_list('currency', flat=True)[0]
        # print("depositaccount_type_and_ntd_amount.get(type__acc_name='原幣定存').get('type__acc_id') >>> ", depositaccount_type_and_ntd_amount.get(type__acc_name='台幣定存').get('type__acc_id'))
        preamt_ntd_cd = preamt_qry_set.get(acc__acc_id=depositaccount_type_and_ntd_amount.get(type__acc_name='原幣定存').get('type__acc_id'))
        # print('台幣定存 preamt >>> ', preamt_ntd_cd)
        preamt_ntd_cd.book_amt = depositaccount_type_and_ntd_amount.get(type__acc_name='原幣定存').get('ntd_amount')
        preamt_ntd_cd.adj_amt = -1 * (deposit_account_qry_set.filter(plege=1, currency=currency).aggregate(Sum('ntd_amount')).get('ntd_amount__sum') \
                         + deposit_account_qry_set.filter(plege=0, currency=currency, end_date__gte=report_end_date + relativedelta(months=3)).aggregate(Sum('ntd_amount')).get('ntd_amount__sum'))
        preamt_ntd_cd.pre_amt = preamt_ntd_cd.book_amt + preamt_ntd_cd.adj_amt
        preamt_ntd_cd.save()
        # print('台幣定存：{}, {}, {}'.format(preamt_ntd_cd.book_amt, preamt_ntd_cd.adj_amt, preamt_ntd_cd.pre_amt))

        # 外幣定存 preamt
        # print("depositaccount_type_and_ntd_amount.get(type__acc_name='外幣定存').get('type__acc_id') >>> ", depositaccount_type_and_ntd_amount.get(type__acc_name='外幣定存').get('type__acc_id'))
        preamt_foreign_currency_cd = preamt_qry_set.get(acc__acc_id=depositaccount_type_and_ntd_amount.get(type__acc_name='外幣定存').get('type__acc_id'))
        # print('外幣定存 preamt >>> ', preamt_foreign_currency_cd)
        preamt_foreign_currency_cd.book_amt = depositaccount_type_and_ntd_amount.get(type__acc_name='外幣定存').get('ntd_amount')
        preamt_foreign_currency_cd.adj_amt = -1 * (deposit_account_qry_set.filter(Q(plege=0) & ~Q(currency='TWD') & Q(end_date__gte=report_end_date + relativedelta(months=3))).aggregate(Sum('ntd_amount')).get('ntd_amount__sum')) \
                            + (list[3]['外幣定存'].amount if list[3]['外幣定存'].credit_debit == 0 else list[3]['外幣定存'].amount*(-1))
        preamt_foreign_currency_cd.pre_amt = preamt_foreign_currency_cd.book_amt + preamt_foreign_currency_cd.adj_amt
        preamt_foreign_currency_cd.save()
        # print('外幣定存：{}, {}, {}'.format(preamt_foreign_currency_cd.book_amt, preamt_foreign_currency_cd.adj_amt, preamt_foreign_currency_cd.pre_amt))


        # # 3. 回傳資料
        # print('尚未測試 fill_in_preamount。 程式碼沒有報錯，但是要檢查金額是否正確。')
        # return {"status_code": 200, "returnObject": ""}
        print('finished fill_in_preamt.')
    except Cashinbanks.DoesNotExist or Depositaccount.DoesNotExist as e:
        print('「銀行存款」或者「定期存款」資料表中沒有對應的 records >>> ', e)
        # return {"status_code": 404, "msg": "無法根據 rpt_id 查詢到「銀行存款」或者「定期存款」。"}

    fill_in_disclosure(preamt_qry_set, rpt_id)

        # TODO 測試時註解掉
        # except Exception as e:
        #     print('發生非預期錯誤 >>> ', e)
        #     return '{"status_code": 500, "msg": "發生非預期錯誤。"}'
    # else:
    #     return {"status_code": 501, "msg": "尚未實作該科目。"}

