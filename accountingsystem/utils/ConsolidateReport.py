from ..models import Cashinbanks, Depositaccount, Adjentry, Preamt, Exchangerate, Report, Account, Company, Group,Reltrx
from django.db import connection


def create_consolidated_report(comp_id,start_date,end_date):
    comp=Company.objects.filter(com_id=comp_id)[0]
    consolidated_report = Report.objects.create(start_date=start_date,end_date=end_date,type='合併',com=comp)
    #consolidated_report = Report.objects.create(start_date='2020-01-01',end_date='2020-12-31',type='合併',com=a)
    return consolidated_report.rpt_id

def create_consolidated_report_preamt(rpt_id,comp_id,start_date,end_date):
    #現金及約當現金
    create_consolidated_report_cash_preamt(rpt_id,comp_id,start_date,end_date)
    #其他待做

#現金及約當現金
def create_consolidated_report_cash_preamt(rpt_id,comp_id,start_date,end_date):
    def check_null_or_not(i,amt):
        if not i:
            i=0
        else:
            i=i.values()[0][amt]
        return i
    #此處的rpt_id是consolidated_report的id#comp_id=母公司
    total_book_amt_demand_deposit=0 #活期存款book_amt
    total_book_amt_check_deposit=0 #支票存款book_amt
    total_book_amt_foreign_currency_deposit=0 #外匯存款book_amt
    total_book_amt_currency_cd=0 #原幣定存book_amt
    total_book_amt_foreign_currency_cd=0 #外幣定存book_amt
    total_adj_amt_demand_deposit=0#活期存款adj_amt
    total_adj_amt_check_deposit=0#支票存款adj_amt
    total_adj_amt_foreign_currency_deposit=0#外匯存款adj_amt
    total_adj_amt_currency_cd=0#原幣定存adj_amt
    total_adj_amt_foreign_currency_cd=0#外幣定存adj_amt
    #撈出母公司所屬的集團
    group_id=Company.objects.filter(com_id=comp_id).values()[0]['grp_id']
    #撈出同個集團的所有公司
    com_list=Company.objects.filter(grp=group_id)
    #撈出母公司幣別
    parent_currency=Company.objects.filter(com_id=comp_id).values()[0]['currency']
    #撈出母公司rpt_id，以便在下方撈出匯率
    parent_rpt_id=Report.objects.filter(com_id=comp_id).filter(start_date=start_date).filter(end_date=end_date).values()[0]['rpt_id']
    for i in com_list:
        com_list[0]
        #查看該公司所使用的幣別
        currency=Company.objects.filter(com_id=i.com_id).values()[0]['currency']
        #currency=Company.objects.filter(com_id=com_list[0].com_id).values()[0]['currency']
        #撈出該公司個體報表rpt_id(報表要是個體,且報表符合所選日期)
        report_id=Report.objects.filter(com=i).filter(type='個體').filter(start_date=start_date).filter(end_date=end_date).values()[0]['rpt_id']
        #撈活期存款 acc_id=11
        pre_amt_demand_deposit=Preamt.objects.filter(rpt=report_id).filter(acc=11)
        pre_amt_demand_deposit=check_null_or_not(pre_amt_demand_deposit,'pre_amt')
        #撈支票存款 acc_id=14
        pre_amt_check_deposit=Preamt.objects.filter(rpt=report_id).filter(acc=14)
        pre_amt_check_deposit=check_null_or_not(pre_amt_check_deposit,'pre_amt')
        #撈外匯存款 acc_id=17
        pre_amt_foreign_currency_deposit=Preamt.objects.filter(rpt=report_id).filter(acc=17)
        pre_amt_foreign_currency_deposit=check_null_or_not(pre_amt_foreign_currency_deposit,'pre_amt')
        #撈原幣定存 acc_id=21
        pre_amt_currency_cd=Preamt.objects.filter(rpt=report_id).filter(acc=21)
        pre_amt_currency_cd=check_null_or_not(pre_amt_currency_cd,'pre_amt')
        #撈外幣定存 acc_id=22
        pre_amt_foreign_currency_cd=Preamt.objects.filter(rpt=report_id).filter(acc=22)
        pre_amt_foreign_currency_cd=check_null_or_not(pre_amt_foreign_currency_cd,'pre_amt')
        if currency==parent_currency:
            #活期存款 
            total_book_amt_demand_deposit=total_book_amt_demand_deposit+pre_amt_demand_deposit
            #支票存款
            total_book_amt_check_deposit=total_book_amt_check_deposit+pre_amt_check_deposit
            #外匯存款
            total_book_amt_foreign_currency_deposit=total_book_amt_foreign_currency_deposit+pre_amt_foreign_currency_deposit
            #原幣定存
            total_book_amt_currency_cd=total_book_amt_currency_cd+pre_amt_currency_cd
            #外幣定存
            total_book_amt_foreign_currency_cd=total_book_amt_foreign_currency_cd+pre_amt_foreign_currency_cd
        else:
            #撈出匯率
            exchange_rate=Exchangerate.objects.filter(currency_name=currency).filter(rpt=parent_rpt_id).values()[0]['rate']
            #活期存款
            pre_amt_demand_deposit=pre_amt_demand_deposit*exchange_rate
            total_book_amt_demand_deposit=total_book_amt_demand_deposit+pre_amt_demand_deposit
            #支票存款
            pre_amt_check_deposit=pre_amt_check_deposit*exchange_rate
            total_book_amt_check_deposit=total_book_amt_check_deposit+pre_amt_check_deposit
            #外匯存款
            pre_amt_foreign_currency_deposit=pre_amt_foreign_currency_deposit*exchange_rate
            total_book_amt_foreign_currency_deposit=total_book_amt_foreign_currency_deposit+pre_amt_foreign_currency_deposit
            #原幣定存
            pre_amt_currency_cd=pre_amt_currency_cd*exchange_rate
            total_book_amt_currency_cd=total_book_amt_currency_cd+pre_amt_currency_cd
            #外幣定存
            pre_amt_foreign_currency_cd=pre_amt_foreign_currency_cd*exchange_rate
            total_book_amt_foreign_currency_cd=total_book_amt_foreign_currency_cd+pre_amt_foreign_currency_cd
        #計算合併沖銷，撈出每間公司的關係人交易分錄
        #先由每間公司對應的pre_amt_id，再撈出關係人交易，把關係人交易相加。
        #撈活期存款pre_id acc_id=11
        pre_id_demand_deposit=Preamt.objects.filter(rpt=report_id).filter(acc=11).values()[0]['pre_id']
        #再撈出關係人交易
        adj_amt_demand_deposit=Reltrx.objects.filter(pre=pre_id_demand_deposit)
        adj_amt_demand_deposit=check_null_or_not(adj_amt_demand_deposit,'related_amt')
        total_adj_amt_demand_deposit=total_adj_amt_demand_deposit+adj_amt_demand_deposit
        #撈支票存款pre_id acc_id=14
        pre_id_check_deposit=Preamt.objects.filter(rpt=report_id).filter(acc=14).values()[0]['pre_id']
        #再撈出關係人交易
        adj_amt_check_deposit=Reltrx.objects.filter(pre=pre_id_check_deposit)
        adj_amt_check_deposit=check_null_or_not(adj_amt_check_deposit,'related_amt')
        total_adj_amt_check_deposit=total_adj_amt_check_deposit+adj_amt_check_deposit
        #撈外匯存款pre_id acc_id=17
        pre_id_foreign_currency_deposit=Preamt.objects.filter(rpt=report_id).filter(acc=17).values()[0]['pre_id']
        #再撈出關係人交易
        adj_amt_foreign_currency_deposit=Reltrx.objects.filter(pre=pre_id_foreign_currency_deposit)
        adj_amt_foreign_currency_deposit=check_null_or_not(adj_amt_foreign_currency_deposit,'related_amt')
        total_adj_amt_foreign_currency_deposit=total_adj_amt_foreign_currency_deposit+adj_amt_foreign_currency_deposit
        #撈原幣定存pre_id acc_id=21
        pre_id_currency_cd=Preamt.objects.filter(rpt=report_id).filter(acc=21).values()[0]['pre_id']
        #再撈出關係人交易
        adj_amt_currency_cd=Reltrx.objects.filter(pre=pre_id_currency_cd)
        adj_amt_currency_cd=check_null_or_not(adj_amt_currency_cd,'related_amt')
        total_adj_amt_currency_cd=total_adj_amt_currency_cd+adj_amt_currency_cd
        #撈外幣定存pre_id acc_id=22
        pre_id_foreign_currency_cd=Preamt.objects.filter(rpt=report_id).filter(acc=22).values()[0]['pre_id']
        #再撈出關係人交易
        adj_amt_foreign_currency_cd=Reltrx.objects.filter(pre=pre_id_foreign_currency_cd)
        adj_amt_foreign_currency_cd=check_null_or_not(adj_amt_foreign_currency_cd,'related_amt')
        total_adj_amt_foreign_currency_cd=total_adj_amt_foreign_currency_cd+adj_amt_foreign_currency_cd
    #撈出rpt_id object
    rpt_id=Report.objects.filter(rpt_id=rpt_id)[0]
    #建立合併報表活期存款preamt
    demand_deposit_acc_id=Account.objects.filter(acc_id=11)[0]
    demand_deposit=Preamt.objects.create(book_amt=total_book_amt_demand_deposit,adj_amt=total_adj_amt_demand_deposit
                                        ,pre_amt=total_book_amt_demand_deposit+total_adj_amt_demand_deposit
                                        ,rpt=rpt_id,acc=demand_deposit_acc_id)
    #建立合併報表支票存款preamt                        
    check_deposit_acc_id=Account.objects.filter(acc_id=14)[0]
    check_deposit=Preamt.objects.create(book_amt=total_book_amt_check_deposit,adj_amt=total_adj_amt_check_deposit
                                        ,pre_amt=total_book_amt_check_deposit+total_adj_amt_check_deposit
                                        ,rpt=rpt_id,acc=check_deposit_acc_id)
    #建立合併報表外匯存款preamt
    foreign_currency_deposit_acc_id=Account.objects.filter(acc_id=17)[0]
    foreign_currency_deposit=Preamt.objects.create(book_amt=total_book_amt_foreign_currency_deposit,adj_amt=total_adj_amt_foreign_currency_deposit
                                        ,pre_amt=total_book_amt_foreign_currency_deposit+total_adj_amt_foreign_currency_deposit
                                        ,rpt=rpt_id,acc=foreign_currency_deposit_acc_id)
    #建立合併報表原幣定存preamt
    currency_cd_acc_id=Account.objects.filter(acc_id=21)[0]
    currency_cd=Preamt.objects.create(book_amt=total_book_amt_currency_cd,adj_amt=total_adj_amt_currency_cd
                                        ,pre_amt=total_book_amt_currency_cd+total_adj_amt_currency_cd
                                        ,rpt=rpt_id,acc=currency_cd_acc_id)
    #建立合併報表外幣定存preamt
    foreign_currency_cd_acc_id=Account.objects.filter(acc_id=22)[0]
    foreign_currency_cd=Preamt.objects.create(book_amt=total_book_amt_foreign_currency_cd,adj_amt=total_adj_amt_foreign_currency_cd
                                        ,pre_amt=total_book_amt_foreign_currency_cd+total_adj_amt_foreign_currency_cd
                                        ,rpt=rpt_id,acc=foreign_currency_cd_acc_id)

    print(total_book_amt_demand_deposit)
    print(total_book_amt_check_deposit)
    print(total_book_amt_foreign_currency_deposit)
    print(total_book_amt_currency_cd)
    print(total_book_amt_foreign_currency_cd)
    print(total_adj_amt_demand_deposit)
    print(total_adj_amt_check_deposit)
    print(total_adj_amt_foreign_currency_deposit)
    print(total_adj_amt_currency_cd)
    print(total_adj_amt_foreign_currency_cd)
    print('~~')