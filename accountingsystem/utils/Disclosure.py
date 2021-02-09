from ..models import Cashinbanks, Depositaccount, Report, Account, Preamt, Company, Distitle, Disclosure, Disdetail

"""
接在 preamount 後開始建立及調整，不限科目皆可使用
"""

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
                                             dis_title=Distitle.objects.filter(rpt_id=rpt_id).first())
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
    delete_disclosure(acc_id, countIdList, rpt_id)

def delete_disclosure(acc_id, countIdList, rpt_id):
    """
    :param countIdList: 需刪除的 preamount_acc_id_list
    """
    disclosure_list = []
    print('>>> delete_disclosure')
    #print('>>> countIdList:', countIdList)
    for i in range(len(countIdList)):
        # print('countIdList >>> ', countIdList)
        disclosure = Disclosure.objects.filter(pre__acc__acc_id=countIdList[i]).first()
        # print('disclosure >>> ', disclosure)
        if disclosure is not None:
            disclosure_list.append(disclosure.dis_detail_id)
            disclosure.delete()
    delete_disdetail(acc_id, disclosure_list, rpt_id)

def delete_disdetail(acc_id, disclosure_list, rpt_id):
    """
    :param disclosure_list: delete_disclosure 中刪除的 disclosure_id list
    """
    print('>>> delete_disdetail')
    for i in range(len(disclosure_list)):
        disdetail = Disdetail.objects.filter(dis_detail_id=disclosure_list[i])
        disdetail.delete()
    delete_distitle(acc_id, rpt_id)

def delete_distitle(acc_id, rpt_id):
    print('>>> delete_distitle')
    disname = Account.objects.filter(acc_id=acc_id)
    Distitle.objects.filter(dis_name=disname[0].acc_name, rpt_id=rpt_id).delete()
    print(">>> Disclosure deleted successfully.")

def fill_in_disclosure(preamt_qry_set, rpt_id):
    """
    :param preamt_qry_set: 從 fill_in_preamount 接來
    讀 preamt_qry_set 中 pre_id 和 disclosure 相同的，填入 pre_amt
    """
    print('>>> fill_in_disclosure')
    disclosure_list = []
    #print('preamt_qry_set:', preamt_qry_set)
    for preamt in preamt_qry_set:
        disclosure = Disclosure.objects.filter(pre_id=preamt.pre_id)
        disclosure.update(pre_amt=preamt.pre_amt)
        disclosure_list.append(disclosure[0].dis_detail_id)
    fill_in_disdetail(disclosure_list, preamt_qry_set, rpt_id)

def fill_in_disdetail(disclosure_list, preamt_qry_set, rpt_id):
    """
    :param disclosure_list: 從 fill_in_disclosure 來
    讀 disclosure_list 中和 disdetail 的 dis_detail_id 相同的，把 pre_amt 金額填入 row_amt
    """
    print('>>> fill_in_disdetail')
    for i in range(len(disclosure_list)):
        dis_detail = Disdetail.objects.filter(dis_detail_id=disclosure_list[i])\
                    .update(row_amt=preamt_qry_set[i].pre_amt)
    print('>>> finish fill in disclosure and disdetail')