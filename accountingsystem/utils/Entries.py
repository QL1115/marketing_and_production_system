import datetime

from ..models import Cashinbanks, Depositaccount, Report, Account, Systemcode, Exchangerate,Adjentry,Preamt
from django.db import connection
from dateutil.relativedelta import relativedelta
from django.db.models import Sum


def create_preamount_and_adjust_entries_for_project_account(comp_id, rpt_id, acc_id):
    print('create_preamount_and_adjust_entries_for_project_account')
    #建立調整
    create_preamount(comp_id, rpt_id, acc_id)
    #建立分錄
    create_adjust_entries(comp_id, rpt_id, acc_id) 

def create_preamount(comp_id, rpt_id, acc_id):
    #如果科目是現金，建立現金的調整表
    if acc_id==4:
        #create_cash_preamount(rpt_id, acc_id)
        print('create_preamount')

def create_adjust_entries(comp_id, rpt_id, acc_id):
    #如果科目是現金，建立現金的分錄
    if acc_id==4:
        create_cash_adjust_entries(rpt_id, acc_id)
        print('create_adjust_entries')

def create_cash_adjust_entries(rpt_id, acc_id):
    # 建立所有現金的 adjust entry
    print('create_cash_adjust_entries')

    cash_in_bank_qry_set=Cashinbanks.objects.all().values()
    deposit_account_qry_set=Depositaccount.objects.all().values()
    cash_qry_set={ 'cash_in_banks': cash_in_bank_qry_set,'deposit_account': deposit_account_qry_set}

    #定期存款-超過三個月定存
    create_over_3_month_deposit_entry(cash_qry_set, rpt_id)
    #定期存款-質押存款
    create_pledge_deposit_account_entry(cash_qry_set,rpt_id)
    #銀行存款-外匯存款
    create_foreign_currency_deposit_entry(cash_qry_set,rpt_id)
    #銀行存款-外幣定存
    create_foreign_currency_time_deposit(cash_qry_set,rpt_id)
    #銀行存款-超過三個月定存
    create_over_three_month_time_deposit(cash_qry_set,rpt_id)


#銀行存款-外匯存款
def create_foreign_currency_deposit_entry(cash_qry_set,rpt_id):
    cash_in_banks=cash_qry_set['cash_in_banks']
    total_difference=0
    exchangerate=0
    for cash_in_bank in cash_in_banks:
        if cash_in_bank['currency']!='TWD':
            #exchangerate
            exchangerate=Exchangerate.objects.filter(currency_name=cash_in_bank['currency']).filter(rpt_id=rpt_id)[0].rate
            difference=(exchangerate*cash_in_bank['foreign_currency_amount'])-cash_in_bank['ntd_amount']
            total_difference=total_difference+difference
    #撈出最大的adj_num
    bigest_adj_num=0
    cursor1 = connection.cursor() 
    cursor1.execute("select count(*) from Adjentry")
    aleady_entry=cursor1.fetchall()[0][0]
    if aleady_entry==0:
        bigest_adj_num=0
    else:
        bigest_adj_num=bigest_num=Adjentry.objects.latest('adj_num').adj_num
    #撈出外匯存款preamt object
    foreign_curency_deposit＿pre_id=Preamt.objects.filter(rpt_id=rpt_id).filter(acc_id=17)[0]
    #建立分路#借兌換損失貸外匯存款
    if total_difference<0:
        #撈出兌換損失pre object
        foreign_exchange_lost＿pre_id=Preamt.objects.filter(rpt_id=rpt_id).filter(acc_id=25)[0]
        #寫入adjentry前，total_difference要先轉成正
        total=total_difference*-1
        #寫入adjentry
        credit_foreign_exchange_losses=Adjentry.objects.create(amount=total,adj_num=bigest_adj_num+1,pre=foreign_exchange_lost＿pre_id,credit_debit=0,front_end_location=2)
        debit_foreign_currency_deposit=Adjentry.objects.create(amount=total,adj_num=bigest_adj_num+1,pre=foreign_curency_deposit＿pre_id,credit_debit=1,front_end_location=2)
        return(credit_foreign_exchange_losses,debit_foreign_currency_deposit)
    #建立分路#借外匯存款貸兌換利益
    elif total_difference>0:
        #撈出兌換利益pre object
        foreign_exchange_gain＿pre_id=Preamt.objects.filter(rpt_id=rpt_id).filter(acc_id=26)[0]
        #寫入adjentry
        credit_foreign_currency_deposit=Adjentry.objects.create(amount=total_difference,adj_num=bigest_adj_num+1,pre=foreign_curency_deposit＿pre_id,credit_debit=0,front_end_location=2)
        debit_foreign_exchange_gain=Adjentry.objects.create(amount=total_difference,adj_num=bigest_adj_num+1,pre=foreign_exchange_gain＿pre_id,credit_debit=1,front_end_location=2)
        return(debit_foreign_exchange_gain,credit_foreign_currency_deposit)

#銀行存款-外幣定存
#此method請放在定期存款調整後
def create_foreign_currency_time_deposit(cash_qry_set,rpt_id):
    exchangerate=0
    total_difference=0
    #重新撈定期存款，因為會需要查看有沒有調整
    deposit_accounts=Depositaccount.objects.all().values()
    for deposit_account in deposit_accounts:
        if deposit_account['currency']!='TWD' and deposit_account['already_adjust']!=1:
             #exchangerate
            exchangerate=Exchangerate.objects.filter(currency_name=deposit_account['currency']).filter(rpt_id=rpt_id)[0].rate
            difference=(exchangerate*deposit_account['foreign_currency_amount'])-deposit_account['ntd_amount']
            total_difference=total_difference+difference
    #撈出最大的adj_num
    bigest_adj_num=0
    cursor1 = connection.cursor() 
    cursor1.execute("select count(*) from Adjentry")
    aleady_entry=cursor1.fetchall()[0][0]
    if aleady_entry==0:
        bigest_adj_num=0
    else:
        bigest_adj_num=bigest_num=Adjentry.objects.latest('adj_num').adj_num
    #撈出外幣定存preamt object
    foreign_curency_time_deposit＿pre_id=Preamt.objects.filter(rpt_id=rpt_id).filter(acc_id=22)[0]
    #建立分路#借兌換損失貸外匯存款
    if total_difference<0:
        #撈出兌換損失pre object
        foreign_exchange_lost＿pre_id=Preamt.objects.filter(rpt_id=rpt_id).filter(acc_id=25)[0]
        #寫入adjentry前，total_difference要先轉成正
        total=total_difference*-1
        #寫入adjentry
        credit_foreign_exchange_losses=Adjentry.objects.create(amount=total,adj_num=bigest_adj_num+1,pre=foreign_exchange_lost＿pre_id,credit_debit=0,front_end_location=2)
        debit_foreign_currency_time_deposit=Adjentry.objects.create(amount=total,adj_num=bigest_adj_num+1,pre=foreign_curency_time_deposit＿pre_id,credit_debit=1,front_end_location=2)
        return(credit_foreign_exchange_losses,debit_foreign_currency_time_deposit)
    #建立分路#借外匯存款貸兌換利益
    elif total_difference>0:
        #撈出兌換利益pre object
        foreign_exchange_gain＿pre_id=Preamt.objects.filter(rpt_id=rpt_id).filter(acc_id=26)[0]
        #寫入adjentry
        credit_foreign_currency_time_deposit=Adjentry.objects.create(amount=total_difference,adj_num=bigest_adj_num+1,pre=foreign_curency_time_deposit＿pre_id,credit_debit=0,front_end_location=2)
        debit_foreign_exchange_gain=Adjentry.objects.create(amount=total_difference,adj_num=bigest_adj_num+1,pre=foreign_exchange_gain＿pre_id,credit_debit=1,front_end_location=2)
        return(debit_foreign_exchange_gain,credit_foreign_currency_time_deposit)

          
#銀行存款-超過三個月定存 
def create_over_three_month_time_deposit(cash_qry_set,rpt_id):
    exchangerate=0
    total_difference=0
    #重新撈定期存款，因為會需要查看有沒有調整
    deposit_accounts=Depositaccount.objects.all().values()
    for deposit_account in deposit_accounts:
        if deposit_account['currency']!='TWD' and deposit_account['already_adjust']==1 and deposit_account['plege']==0:
            #exchangerate
            exchangerate=Exchangerate.objects.filter(currency_name=deposit_account['currency']).filter(rpt_id=rpt_id)[0].rate
            difference=(exchangerate*deposit_account['foreign_currency_amount'])-deposit_account['ntd_amount']
            total_difference=total_difference+difference
    #撈出最大的adj_num
    bigest_adj_num=0
    cursor1 = connection.cursor() 
    cursor1.execute("select count(*) from Adjentry")
    aleady_entry=cursor1.fetchall()[0][0]
    if aleady_entry==0:
        bigest_adj_num=0
    else:
        bigest_adj_num=bigest_num=Adjentry.objects.latest('adj_num').adj_num
    #撈出超過三個月定存preamt object
    over_three_month_time_deposit＿pre_id=Preamt.objects.filter(rpt_id=rpt_id).filter(acc_id=23)[0]
    if total_difference<0:
        #撈出兌換損失pre object
        foreign_exchange_lost＿pre_id=Preamt.objects.filter(rpt_id=rpt_id).filter(acc_id=25)[0]
        #寫入adjentry前，total_difference要先轉成正
        total=total_difference*-1
        #寫入adjentry
        credit_foreign_exchange_losses=Adjentry.objects.create(amount=total,adj_num=bigest_adj_num+1,pre=foreign_exchange_lost＿pre_id,credit_debit=0,front_end_location=2)
        debit_over_three_month_time_deposit=Adjentry.objects.create(amount=total,adj_num=bigest_adj_num+1,pre=over_three_month_time_deposit＿pre_id,credit_debit=1,front_end_location=2)
        return(credit_foreign_exchange_losses,debit_over_three_month_time_deposit)
    #建立分路#借外匯存款貸兌換利益
    elif total_difference>0:
        #撈出兌換利益pre object
        foreign_exchange_gain＿pre_id=Preamt.objects.filter(rpt_id=rpt_id).filter(acc_id=26)[0]
        #寫入adjentry
        credit_over_three_month_time_deposit=Adjentry.objects.create(amount=total_difference,adj_num=bigest_adj_num+1,pre=over_three_month_time_deposit＿pre_id,credit_debit=0,front_end_location=2)
        debit_foreign_exchange_gain=Adjentry.objects.create(amount=total_difference,adj_num=bigest_adj_num+1,pre=foreign_exchange_gain＿pre_id,credit_debit=1,front_end_location=2)
        return(debit_foreign_exchange_gain,credit_over_three_month_time_deposit)

#定期存款-超過三個月定存
def create_over_3_month_deposit_entry(cash_qry_set, rpt_id):
    #建立超過三個月定存調整分錄
    print('create_over_3_month_deposit_entry')
    deposit_account = cash_qry_set['deposit_account']
    ntd_total = 0
    foreign_currency_total = 0
    report_start_date = Report.objects.filter(rpt_id=rpt_id).value_list('start_date')

    #計算時間差(月)
    report_start_year = report_start_date[0]['start_date'].year
    report_start_month =report_start_date[0]['start_date'].month
    deposit_year = deposit_account[0]['start_date'].year
    deposit_month = deposit_account[0]['start_date'].month
    duration = 12*(report_start_year-deposit_year)+(report_start_month-deposit_month)

    for deposit_account in deposit_account:
       if duration > 3:
           deposit_account['already_adjusted'] = 1
           if deposit_account['foreign_currency_amount'] != None:
              foreign_currency_total += deposit_account['ntd_amount']
           else:
              ntd_total += deposit_account['ntd_amount']

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
    #(amount, adj_num, pre_id, credit_debit, front_end_location)
    #(ntd_total, 目前最大, preamount.report_id = report_id 的 pre_id, 0, 1)
    credit_ntd_over_3_month_total = Adjentry.objects.create(amount=ntd_total, adj_num=bigest_adj_num + 1,
                                                             pre=over_3_month_pre_id, credit_debit=0,
                                                             front_end_location=1)
    #create_adjust_entry for 台幣定存
    #(amount, adj_num, pre_id, credit_debit, front_end_location)
    #(ntd_total, 目前最大(與上同), preamount.report_id = report_id 的 pre_id, 1, 1)
    debit_ntd_deposit_total = Adjentry.objects.create(amount=ntd_total, adj_num=bigest_adj_num + 1,
                                                             pre=ntd_deposit_pre_id, credit_debit=1,
                                                             front_end_location=1)
    #create_adjust_entry for foreign_currency_over_3_month_total
    #(amount, adj_num, pre_id, credit_debit, front_end_location)
    #(foreign_currency_total, 目前最大(與上同), preamount.report_id = report_id 的 pre_id, 0, 1)
    credit_foreign_currency_over_3_month_total = Adjentry.objects.create(amount=foreign_currency_total, adj_num=bigest_adj_num + 1,
                                                             pre=over_3_month_pre_id, credit_debit=0,
                                                             front_end_location=1)
    #create_adjust_entry for 外幣定存
    #(amount, adj_num, pre_id, credit_debit, front_end_location)
    #(foreign_currency_total, 目前最大(與上同), preamount.report_id = report_id 的 pre_id, 1, 1)
    debit_foreign_currency_deposit_total = Adjentry.objects.create(amount=foreign_currency_total, adj_num=bigest_adj_num + 1,
                                                             pre=foreign_currency_pre_id, credit_debit=1,
                                                             front_end_location=1)
    return(credit_ntd_over_3_month_total, debit_ntd_deposit_total, credit_foreign_currency_over_3_month_total, debit_foreign_currency_deposit_total )

#定期存款-質押存款
def create_pledge_deposit_account_entry(cash_qry_set, rpt_id):
    print('create_pledge_deposit_account_entry')
    pledge_total = 0
    deposit_account = cash_qry_set['deposit_account']
    new_deposit_account=[]
    for deposit_account in deposit_account:
        if deposit_account['already_adjusted']==0:
            new_deposit_account.add(deposit_account)

    for deposit_account in new_deposit_account:
       if deposit_account['pledge'] == 1:
           pledge_total += deposit_account['ntd_amount']

    '''撈出最大的adj_num(可以寫一個method)'''
    cursor1 = connection.cursor()
    cursor1.execute("select count(*) from Adjentry")
    aleady_entry=cursor1.fetchall()[0][0]
    if aleady_entry==0:
        bigest_adj_num=0
    else:
        bigest_adj_num=Adjentry.objects.latest('adj_num').adj_num

    #撈出 preamount id
    pledge_pre_id = Preamt.objects.filter(rpt_id=rpt_id).filter(acc_id=24)[0]
    ntd_deposit_pre_id = Preamt.objects.filter(rpt_id=rpt_id).filter(acc_id=21)[0]

    #create_adjust_entry_for_pledge
    #(amount, adj_num, pre_id, credit_debit, front_end_location)
    #(pledge_total, 目前最大(與上同), preamount.report_id = report_id 的 pre_id, 0, 1)
    credit_pledge_total = Adjentry.objects.create(amount=pledge_total, adj_num=bigest_adj_num + 1,
                                                             pre=pledge_pre_id, credit_debit=0,
                                                             front_end_location=1)
    #create_adjust_entry_for_台幣定存
    #(amount, adj_num, pre_id, credit_debit, front_end_location)
    #(pledge_total, 目前最大(與上同), preamount.report_id = report_id 的 pre_id, 1, 1)
    debit_ntd_deposit_total = Adjentry.objects.create(amount=pledge_total, adj_num=bigest_adj_num + 1,
                                                             pre=ntd_deposit_pre_id, credit_debit=1,
                                                             front_end_location=1)
    return(credit_pledge_total, debit_ntd_deposit_total )

def create_cash_preamount(rpt_id, acc_id):
    print('create_cash_preamount')


def fill_in_preamount(list,  rpt_id, acc_id):
    '''
    將 adjust entry 中計算完成的 preamount 塞回。
    :param list: eg. [{"質押定存": 質押定存obj, "台幣定存": 台幣定存obj}, {"外匯存款", 外匯存款obj}, {...}, ...]
    :return JSON format string，代表成功或失敗
    '''

    # if acc_id == 1: # TODO 待確定，這個科目到底是 「現金及約當現金(id: 1)」還是「現金(id: 4)」?
    try:
        # 1. 撈 cashinbank 及 depositaccount 這兩個 table 內的 type，找出對應的 account id 後決定邏輯。
        cash_in_bank_qry_set = Cashinbanks.objects.filter(rpt__rpt_id=rpt_id)
        cashinbank_type_and_ntd_amount = cash_in_bank_qry_set.values('type__acc_id', 'type__acc_name').annotate(ntd_amount = Sum('ntd_amount'))
        # print('cashinbank.query >>> ', cashinbank_type_and_ntd_amount.query)
        print('cashinbank_type_and_ntd_amount >>> ', cashinbank_type_and_ntd_amount)
        deposit_account_qry_set = Depositaccount.objects.filter(rpt__rpt_id=rpt_id)
        depositaccount_type_and_ntd_amount = deposit_account_qry_set.values('type__acc_id', 'type__acc_name').annotate(ntd_amount = Sum('ntd_amount'))
        # print('depositaccount.query >>> ', depositaccount_type_and_ntd_amount.query)
        print('depositaccount_type_and_ntd_amount >>> ', depositaccount_type_and_ntd_amount)

        # 使用上傳資料表的 type 的 acc id 和 rpt_id 查出對應的 preamount qry set
        rpt_acc_tuples = tuple([(rpt_id, item['type__acc_id']) for item in cashinbank_type_and_ntd_amount.values('type__acc_id')]) + tuple([(rpt_id, item['type__acc_id']) for item in depositaccount_type_and_ntd_amount.values('type__acc_id')])
        print('rpt_acc_tuples >>> ', rpt_acc_tuples)
        # 寫法參考：https://stackoverflow.com/a/41717889
        preamt_qry_set = Preamt.objects.extra(where=['(rpt_id, acc_id) in %s'], params=[rpt_acc_tuples])
        print('preamt_qry_set >>> ', preamt_qry_set)
        # preamt53 = preamt_qry_set.get(acc__acc_id=53)
        # print('preamt53 >>> ', preamt53)

        # 各個不同 account 的邏輯
        # 目前 list 中 index，0: 超過三個月定存＿entry(), 1: 質押定存＿entry(), 2: 外匯存款＿entry(), 3: 外幣定存＿entry(), 4: 超過三個月定存匯率差_entry()
        # TODO 「活期存款」和「支票存款」目前沒有例子，故暫時不調。目前只調整「外幣存款」、「台幣定存」、「外幣定存」
        # adj_demand_deposit: 活期存款調整數, adj_check_deposit: 支票存款調整數, adj_foreign_currency_deposit: 外匯存款調整數, adj_exchange_loss: 兌換損失, adj_exchange_gain: 兌換利益
        # adj_foreign_currency_cd: 外幣定存調整數, adj_ntd_cd: 台幣定存調整數, adj_exceed_three_months_dp: 超過三個月定存, adj_pledge: 質押定存

        # print('<調整數> 超過三個月定存 {:f}, 台幣定存 {:f}, 外幣定存 {:f}, 質押定存 {:f}, 外匯存款 {:f}, 兌換利益 {:f}, 兌換損失 {:f} ')
        print('!!!!!!', datetime.date(year=2019,month=12,day=31) + relativedelta(months=3))

        # 2. 設置 preamt value
        # 活期存款 preamt
        preamt_demand_deposit = preamt_qry_set.get(acc__acc_id=cashinbank_type_and_ntd_amount.get(type__acc_name='活期存款').get('type__acc_id'))
        preamt_demand_deposit.book_amt = cashinbank_type_and_ntd_amount.get(type__acc_name='活期存款').get('ntd_amount')
        preamt_demand_deposit.adj_mat = 0 # TODO
        preamt_demand_deposit.pre_amt = preamt_demand_deposit.book_amt + preamt_demand_deposit.adj_mat
        # TODO preamt_demand_deposit.save()
        # 支票存款 preamt
        preamt_check_deposit = preamt_qry_set.get(acc__acc_id=cashinbank_type_and_ntd_amount.get(type__acc_name='支票存款').get('type__acc_id'))
        preamt_check_deposit.book_amt = cashinbank_type_and_ntd_amount.get(type__acc_name='支票存款').get('ntd_amount')
        preamt_check_deposit.adj_mat = 0  # TODO
        preamt_check_deposit.pre_amt = preamt_check_deposit.book_amt + preamt_check_deposit.adj_mat
        # TODO preamt_check_deposit.save()
        # 外匯存款 preamt
        preamt_foreign_currency_deposit = preamt_qry_set.get(acc__acc_id=cashinbank_type_and_ntd_amount.get(type__acc_name='外匯存款').get('type__acc_id'))
        preamt_foreign_currency_deposit.book_amt = cashinbank_type_and_ntd_amount.get(type__acc_name='外匯存款').get('ntd_amount')
        preamt_foreign_currency_deposit.adj_mat = list[2]['外匯存款'].amount if list[2]['外匯存款'].credit_debit == 0 else list[2]['外匯存款'].amount*(-1)
        preamt_foreign_currency_deposit.pre_amt = preamt_foreign_currency_deposit.book_amt + preamt_foreign_currency_deposit.adj_mat
        # TODO preamt_foreign_currency_deposit.save()
        # 台幣定存 preamt
        preamt_ntd_cd = preamt_qry_set.get(acc__acc_id=depositaccount_type_and_ntd_amount.get(type__acc_name='台幣定存').get('type__acc_id'))
        preamt_ntd_cd.book_amt = depositaccount_type_and_ntd_amount.get(type__acc_name='台幣定存').get('ntd_amount')
        preamt_ntd_cd.adj_mat = -1 * (deposit_account_qry_set.filter(plege=1).aggregate(Sum('ntd_amount')).get('ntd_amount__sum') \
                         + deposit_account_qry_set.filter(plege=0, end_date__gte=datetime.date(year=2019,month=12,day=31) + relativedelta(months=3)).aggregate(Sum('ntd_amount')).get('ntd_amount__sum'))
        preamt_ntd_cd.pre_amt = preamt_ntd_cd.book_amt + preamt_ntd_cd.adj_mat
        # TODO ntd_cd.save()
        # 外幣定存 preamt
        preamt_foreign_currency_cd = preamt_qry_set.get(acc__acc_id=deposit_account_qry_set.get(type__acc_name='外幣定存').get('type__acc_id'))
        preamt_foreign_currency_cd.book_amt = depositaccount_type_and_ntd_amount.get(type__acc_name='外幣定存').get('ntd_amount')
        preamt_foreign_currency_cd.adj_mat = -1 * (deposit_account_qry_set.filter(plege=0,type__acc_name='外幣定存', end_date__gte=datetime.date(year=2019,month=12,day=31) + relativedelta(months=3)).aggregate(Sum('ntd_amount')).get('ntd_amount__sum')
                            + list[3]['外幣定存'].amount if list[3]['外幣定存'].credit_debit == 0 else list[3]['外幣定存'].amount*(-1))
        preamt_foreign_currency_cd.pre_amt = preamt_foreign_currency_cd.book_amt + preamt_foreign_currency_cd.adj_mat
        # TODO foreign_currency_cd.save()

        # # 3. 回傳資料
        # print('尚未測試 fill_in_preamount。 程式碼沒有報錯，但是要檢查金額是否正確。')
        return {"status_code": 200, "returnObject": ""}
    except Cashinbanks.DoesNotExist or Depositaccount.DoesNotExist as e:
        print('「銀行存款」或者「定期存款」資料表中沒有對應的 records >>> ', e)
        return {"status_code": 404, "msg": "無法根據 rpt_id 查詢到「銀行存款」或者「定期存款」。"}

        # TODO 測試時註解掉
        # except Exception as e:
        #     print('發生非預期錯誤 >>> ', e)
        #     return '{"status_code": 500, "msg": "發生非預期錯誤。"}'
    # else:
    #     return {"status_code": 501, "msg": "尚未實作該科目。"}





