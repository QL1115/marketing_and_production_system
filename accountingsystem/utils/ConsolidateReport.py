from ..models import Cashinbanks, Depositaccount, Adjentry, Preamt, Exchangerate, Report, Account, Company, Group, Reltrx, Distitle, Disdetail, Disclosure
from django.db import connection
import math


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
    # 建立Distitle, Disdetail, Disclosure
    create_disclosure_for_consolidated_report_by_acc_id(rpt_id, comp_id, start_date, end_date, 1) # 現金及約當現金的acc_id為1(建Preamt時是寫死的，這裡acc_id也暫時先直接寫死)
    
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

def create_disclosure_for_consolidated_report_by_acc_id(rpt_id,comp_id,start_date,end_date, acc_id):
    '''合併報表附註格式設定需參考母公司在個體報表時的設定，故不採用個體報表時建立Disclosure的方法'''
    print('create disclosure series..')
    # 建立Distitle
    acc_name = Account.objects.get(acc_id=acc_id).acc_name
    distitle = Distitle.objects.create(dis_name=acc_name, rpt=rpt_id)
    # 根據母公司的附註格式設定建立Disdetail
    raw_cursor = connection.cursor()    
    cre_disdetail = ''' 
                       INSERT INTO Disdetail(row_name, row_amt, dis_title_id)
                        SELECT DISTINCT A.row_name, 0 AS row_amt, dis_title_param as dis_title_id 
                        FROM Disdetail A
                        INNER JOIN Distitle B ON A.dis_title_id = B.dis_title_id
                        INNER JOIN Report C ON B.rpt_id = C.rpt_id
                        -- 只能撈出指定科目的Disdetail -> 需Join Disclosure/Preamt/Account確認撈出來的Disdetail的acc_parent是指定的acc_id
                        INNER JOIN Disclosure D ON A.dis_detail_id = D.dis_detail_id
                        INNER JOIN Preamt E ON D.pre_id = E.pre_id
                        INNER JOIN Account F ON E.acc_id = F.acc_id
                        INNER JOIN Account G ON F.acc_parent = G.acc_id
                        WHERE A.row_amt != 0 AND C.com_id = com_param AND C.type = '個體' AND C.start_date = \'start_date_param\' AND C.end_date = \'end_date_param\'
                              AND G.acc_parent = acc_param'''\
                       .replace('dis_title_param', str(distitle.dis_title_id)).replace('com_param', str(comp_id))\
                       .replace('start_date_param', str(start_date)).replace('end_date_param', str(end_date)).replace('acc_param', str(acc_id))
    print(cre_disdetail)
    raw_cursor.execute(cre_disdetail)
    print('-'*100)
    # 根據Disdetail跟Disclosure的關係建立Disclosure
    cre_disclosure = '''
                        INSERT INTO Disclosure(pre_amt, dis_detail_id, pre_id)
                        SELECT A.pre_amt, C.dis_detail_id, A.pre_id
                        FROM (
                            -- 合併Report新建立的Preamt
                            SELECT * FROM Preamt WHERE rpt_id = rpt_param
                        ) A
                        INNER JOIN (
                            -- 母公司個體Report下Disclosure及Disdetail的關係
                            SELECT E.acc_id, A.*, B.row_name, B.row_amt, B.dis_title_id, AA.acc_parent AS parent, AAA.acc_parent AS ancestor
                            FROM Disclosure A
                            INNER JOIN Preamt E ON A.pre_id = E.pre_id
                            INNER JOIN Account AA ON E.acc_id = AA.acc_id
                            INNER JOIN Account AAA ON AA.acc_parent = AAA.acc_id
                            INNER JOIN Disdetail B ON A.dis_detail_id = B.dis_detail_id
                            INNER JOIN Distitle C ON B.dis_title_id = C.dis_title_id
                            INNER JOIN Report D ON C.rpt_id = D.rpt_id
                            WHERE A.pre_amt != 0 AND D.com_id = com_param AND D.type = '個體' AND D.start_date = \'start_date_param\' AND D.end_date = \'end_date_param\'
                                  AND AAA.acc_parent = acc_param -- Disclosure這裡存的都是level 1的科目 直接確認最上層acc_parent(level 3)是指定的acc_id就可以惹
                        ) B ON A.acc_id = B.acc_id
                        INNER JOIN (
                            -- 合併Report新建立的Disdetail
                            SELECT * FROM Disdetail WHERE dis_title_id = dis_title_param
                        ) C ON B.row_name = C.row_name''' \
                       .replace('rpt_param', str(rpt_id.rpt_id)).replace('dis_title_param', str(distitle.dis_title_id)).replace('com_param', str(comp_id))\
                       .replace('start_date_param', str(start_date)).replace('end_date_param', str(end_date)).replace('acc_param', str(acc_id))
    print(cre_disclosure)
    raw_cursor.execute(cre_disclosure)
    print('-'*100)
    # 建立Disdetail的時候row_amt是塞0，Disclosure建立完後要來更新Disdetail的row_amt
    update_disdetail = '''
                        UPDATE
                        Disdetail AS dest,
                        (
                            SELECT SUM(A.pre_amt) AS summ,  A.dis_detail_id
                            FROM Disclosure A
                            INNER JOIN Preamt B ON A.pre_id = B.pre_id
                            INNER JOIN Report C ON B.rpt_id = C.rpt_id
                            -- INNER JOIN Account D ON B.acc_id = D.acc_id
                            WHERE C.rpt_id = rpt_param AND B.pre_amt != 0
                            GROUP BY A.dis_detail_id
                        ) AS src
                        SET
                           dest.row_amt = src.summ
                        WHERE
                            dest.dis_detail_id = src.dis_detail_id'''\
                       .replace('rpt_param', str(rpt_id.rpt_id))
    print(update_disdetail)
    raw_cursor.execute(update_disdetail)

    print('-'*100)
    total_disdetail=0
    round_disdetail_dict={}
    round_total_disdetail=0
    def normal_round(amt):
        if amt/1000 - math.floor(amt/1000) < 0.5:
            return math.floor(amt/1000)
        else:
            return math.ceil(amt/1000)
    disdetail_qry_set = Disdetail.objects.filter(dis_title__rpt_id=rpt_id, dis_title__dis_title_id = distitle.dis_title_id).order_by("row_name").values()
    print(disdetail_qry_set)
    print('rpt_id',rpt_id)
    print('distitle.dis_title_id',distitle.dis_title_id)
    print('!')
    for i in disdetail_qry_set:
        print(i)

        disdetail = Disdetail.objects.get(dis_detail_id=i['dis_detail_id']) # 原本loop query set取出來的會是dict,因為要update金額進DB，拿dict的dis_detail_id去拿出object
        row_amt = disdetail.row_amt
        total_disdetail=total_disdetail+row_amt
        # 千元表示
        row_amt_in_thou = normal_round(row_amt)
        round_total_disdetail+=row_amt_in_thou
        # update千元表示金額至DB
        disdetail.row_amt_in_thou = row_amt_in_thou
        disdetail.save()
        print('savedis')
    print('Create distitle/disdetail/disclosure successfully.')

def delete_consolidate_report(comp_id, rpt_id):
    #被呼叫到地方在views.py中的def delete_file()＆def update_raw_file()中
    def check_null_or_not(i,amt):
        if not i:
            i=0
        else:
            i=i.values()[0][amt]
        return i
    #撈出母公司所屬的集團
    group_id=Company.objects.filter(com_id=comp_id).values()[0]['grp_id']
    #撈出同個集團的所有公司
    com_list=Company.objects.filter(grp=group_id)
    #撈出該rpt的start_date:
    start_date=Report.objects.filter(rpt_id=rpt_id).values()[0]['start_date']
    #撈出該rpt的end_date
    end_date=Report.objects.filter(rpt_id=rpt_id).values()[0]['end_date']
    for i in com_list:
        #.values()[0]['rpt_id']
        #com_id=com_list[0]
        #撈出該公司個體報表rpt_id(報表要是個體,且報表符合所選日期)
        report_id=Report.objects.filter(com=i).filter(type='合併').filter(start_date=start_date).filter(end_date=end_date)
        #report_id=Report.objects.filter(com=com_id).filter(type='合併').filter(start_date=start_date).filter(end_date=end_date)
        if not report_id:
            pass
        else:
            report_id=report_id.values()[0]['rpt_id']
            Report.objects.filter(rpt_id=report_id).delete()


