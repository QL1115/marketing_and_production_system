
from ..models import Cashinbanks, Depositaccount, Report, Account, Systemcode


def create_preamount_and_adjust_entries_for_project_account(comp_id, rpt_id, acc_id):
    print('create_preamount_and_adjust_entries_for_project_account')
    #建立調整
    create_preamount(comp_id, rpt_id, acc_id)
    #建立分錄
    create_adjust_entries(comp_id, rpt_id, acc_id) 



def create_preamount(comp_id, rpt_id, acc_id):
    #如果科目是現金，建立現金的調整表
    if acc_id==4:
        create_cash_preamount(rpt_id, acc_id)
        print('create_preamount')


def create_adjust_entries(comp_id, rpt_id, acc_id):
    #如果科目是現金，建立現金的分錄
    if acc_id==4:
        create_cash_adjust_entries(rpt_id, acc_id)
        print('create_adjust_entries')


def create_cash_adjust_entries(rpt_id, acc_id):
    print('create_cash_adjust_entries')



def create_cash_preamount(rpt_id, acc_id):
    print('create_cash_preamount')


def fill_in_preamount(list, rpt_id, acc_id):
    '''
    將 adjust entry 中計算完成的 preamount 塞回。
    :param list: eg. [{"質押定存": 質押定存obj, "台幣定存": 台幣定存obj}, {"外匯存款", 外匯存款obj}, {...}, ...]
    :return JSON format string，代表成功或失敗
    '''
    try:
        # 1. 撈 cashinbank 及 depositaccount 這兩個 table 內的 type，找出對應的 account id 後決定邏輯。
        cash_in_bank = Cashinbanks.objects.get(rpt__rpt_id=rpt_id)
        deposit_account = Depositaccount.objects.get(rpt__rpt_id=rpt_id)
        # 2. 各個不同 account id 的邏輯

    except Cashinbanks.DoesNotExist or Depositaccount.DoesNotExist as e:
        print('「銀行存款」或者「定期存款」資料表中沒有對應的 records >>> ', e)
        return '{"status_code": 404, "msg": "無法根據 rpt_id 查詢到「銀行存款」或者「定期存款」。"}'

















    

    
