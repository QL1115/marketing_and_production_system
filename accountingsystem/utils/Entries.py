
from ..models import Cashinbanks, Depositaccount, Report, Account, Systemcode, Exchangerate,Adjentry,Preamt
from django.db import connection

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
    cash_in_bank_qry_set=Cashinbanks.objects.all().values()
    deposit_account_qry_set=Depositaccount.objects.all().values()
    cash_qry_set={ 'cash_in_banks': cash_in_bank_qry_set,'deposit_account': deposit_account_qry_set}
    #銀行存款-外匯存款
    create_foreign_currency_deposit＿entry(cash_qry_set,rpt_id)
    #銀行存款-外幣定存
    create_foreign_currency_time_deposit(cash_qry_set,rpt_id)
    #銀行存款-超過三個月定存
    create_over_three_month_time_deposit(cash_qry_set,rpt_id)
    

#銀行存款-外匯存款
def create_foreign_currency_deposit＿entry(cash_qry_set,rpt_id):
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
    

def create_cash_preamount(rpt_id, acc_id):
    print('create_cash_preamount')



