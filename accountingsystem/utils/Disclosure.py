from ..models import Cashinbanks, Depositaccount, Report, Account, Preamt, Company, Distitle, Disclosure, Disdetail


def create_disclosure_for_project_account(preamount_list, rpt_id, acc_id):
    """
    目前依順序建立: Preamount > Distitle > DisDetail > Disclosure，
    """
    print('>>> create_disclosure_for_project_account')
    create_distitle(preamount_list, rpt_id, acc_id)

def create_distitle(preamount_list, acc_id, rpt_id):
    """
    根據科目名稱建立 distitle
    """
    print('>>> create_distitle')
    disname = Account.objects.filter(acc_id=acc_id).values('acc_name')
    Distitle.objects.create(dis_name=disname[0]['acc_name'], rpt_id=rpt_id)
    create_disdetail(preamount_list, rpt_id)

def create_disdetail(preamount_list, rpt_id):
    """
    Preamount 建完後傳入 list，從中依序讀 id，建 Disdetail
    """
    print('>>> create_disdetail')
    disdetail_list = []
    for i in preamount_list:
        disdetail = Disdetail.objects.create(row_name=Account.objects.filter(acc_id=i.acc_id).values('acc_name')[0]['acc_name'], row_amt=0,
                                             dis_title=Distitle.objects.get(rpt_id=rpt_id))
        disdetail_list.append(disdetail)
    create_disclosure(preamount_list, disdetail_list, rpt_id)

def create_disclosure(preamount_list, disdetail_list, rpt_id):
    """
    DisDetail 和 Preamount 建完後傳入 list，從中依序讀 id，建 Disclosure
    """
    print('>>> create_disclosure')
    for i in range(len(preamount_list)):
        Disclosure.objects.create(dis_detail_id=disdetail_list[i].dis_detail_id,
                                  pre_id=preamount_list[i].pre_id, pre_amt=0)
    print(">>> Disclosure created successfully.")

def delete_disclosure_for_project_account(acc_id, countIdList, rpt_id):
    print('>>> delete_disclosure_for_project_account')
    delete_distitle(acc_id, countIdList, rpt_id)

def delete_distitle(acc_id, countIdList, rpt_id):
    print('>>> delete_distitle')
    disname = Account.objects.filter(acc_id=acc_id).values('acc_name')
    Distitle.objects.filter(dis_name=disname[0]['acc_name'], rpt_id=rpt_id).delete()
    delete_disdetail(countIdList, rpt_id)

def delete_disdetail(countIdList, rpt_id):
    print('>>> delete_disdetail')
    disdetail_list = []
    for i in countIdList:
        disdetail = Disdetail.objects.filter(row_name=Account.objects.filter(acc_id=i),
                                             dis_title=Distitle.objects.get(rpt_id=rpt_id))
        disdetail_list.append(disdetail.dis_detail_id)
        disdetail.delete()
    delete_disclosure(countIdList, disdetail_list, rpt_id)

def delete_disclosure(countIdList, disdetail_list, rpt_id):
    print('>>> delete_disclosure')
    for i in range(len(countIdList)):
        Disclosure.objects.filter(dis_detail_id=disdetail_list[i],
                                  pre_id=countIdList[i], pre_amt=0)
    print(">>> Disclosure deleted successfully.")


