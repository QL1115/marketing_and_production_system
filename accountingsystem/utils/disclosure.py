from ..models import Cashinbanks, Depositaccount, Report, Account, Preamt, Company, Distitle, Disclosure, Disdetail
from django.db import connection

def create_disclosure_for_project_account(comp_id: object, rpt_id: object, acc_id: object) -> object:
    print('create_disclosure_for_project_account')
    create_distitle(comp_id, rpt_id, acc_id)
    create_disdetail(comp_id, rpt_id, acc_id)
    create_disclosure(comp_id, rpt_id, acc_id)
    print("Disclosure created successfully.")

def create_distitle(comp_id, rpt_id, acc_id):
    #根據科目名稱建立 distitle
    disname = Account.objects.filter(acc_id=acc_id).get('acc_name')
    Distitle.objects.create(disname=disname, rpt_id=rpt_id)

def create_disdetail(comp_id, rpt_id, acc_id):
    Disdetail.objects.create()


def create_disclosure(comp_id, rpt_id, acc_id):
    return {"status_code": 501, "msg": "尚未實作該科目。"}