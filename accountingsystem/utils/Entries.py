
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














    

    
