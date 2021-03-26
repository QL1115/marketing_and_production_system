from builtins import Exception, list, set, len

from ..models import Cashinbanks, Depositaccount, Adjentry, Preamt, Exchangerate, Report, Account, Company, Group, Reltrx, Distitle, Disdetail, Disclosure
from .Common import normal_round
from dateutil.relativedelta import relativedelta

def get_current_and_previous_rpt(current_rpt_id, rpt_type, comp_id):
    '''input: 當期 rpt_id, output: 當期 rpt 和 前期 rpt'''
    try:
        current_rpt = Report.objects.get(rpt_id=current_rpt_id, type=rpt_type, com_id=comp_id)
        # if current_rpt is None:
        #     return None
        rd = relativedelta(current_rpt.end_date + relativedelta(days=1), current_rpt.start_date)
        months_duration = rd.years * 12 + rd.months # 一期為幾個月
        # 推算前一期起始及結束日
        previous_rpt_end_date = current_rpt.start_date - relativedelta(days=1)
        previous_rpt_start_date = previous_rpt_end_date + relativedelta(days=1) - relativedelta(months=months_duration)
        previous_rpt = Report.objects.get(start_date=previous_rpt_start_date, end_date=current_rpt.start_date - relativedelta(days=1), type=rpt_type, com_id=comp_id)
        # if previous_rpt is None:
        #     return
        return current_rpt, previous_rpt
    except Exception as e:
        return None, None

def cal_previous_comparision(base_period, rpt_id, acc_id, rpt_type, comp_id):  # 此處的 acc_id 是 level 3 的。 eg. 現金及約當現金的 id
    '''計算並回傳前期比較。base: 基準，relative: 另一期'''
    # 確認期間是多久，取得「當期 rpt」和「前期 rpt」
    current_rpt, previous_rpt = get_current_and_previous_rpt(rpt_id, rpt_type, comp_id)
    print(current_rpt, previous_rpt)
    if (current_rpt or previous_rpt) is None:
        return None, None
    relative_version_num = 0
    base_version_num = 0
    if previous_rpt is not None:
        base_rpt = None # 基準期的 report
        relative_rpt = None # 另一期的 report
        if base_period == 'now':  # 以「當期」的附註格式為主要格式
            base_rpt = current_rpt
            relative_rpt = previous_rpt
            relative_version_num = 3
            base_version_num = 2
        else: # 以「前期」的附註格式為主要格式
            base_rpt = previous_rpt
            relative_rpt = current_rpt
            relative_version_num = 2
            base_version_num = 3
        relative_disclosures = Disclosure.objects.filter(pre__rpt_id=relative_rpt, pre__rpt__type=rpt_type, pre__rpt__com_id=comp_id,version_num=1).exclude(pre_amt=0)
        base_disclosures = Disclosure.objects.filter(pre__rpt_id=base_rpt, pre__rpt__type=rpt_type, pre__rpt__com_id=comp_id, version_num=1).exclude(pre_amt=0)
        # 查詢 distitle 中的 disname（與 level 3 的 acc_name 是一致的）
        disname = Account.objects.get(acc_id=acc_id).acc_name
        # 查詢兩個 report 的 distitle
        relative_distitle = Distitle.objects.get(rpt_id=relative_rpt.rpt_id, dis_name=disname)
        base_distitle = Distitle.objects.get(rpt_id=base_rpt.rpt_id, dis_name=disname)
        # base disdetail version 1
        base_disdetail = Disdetail.objects.filter(dis_title__rpt_id=base_rpt.rpt_id).exclude(row_amt=0)
        base_disdetail_row_name = list(base_disdetail.values_list('row_name',flat=True).distinct())
        # 先為兩期建立「基準期」擁有的 disdetail
        Disdetail.objects.bulk_create([Disdetail(row_name=row_name, row_amt=0, version_num=relative_version_num, dis_title=relative_distitle) for row_name in base_disdetail_row_name]) # 這裡似乎不會回傳 id 回來
        relative_disdetail_qryset_ver2 = Disdetail.objects.filter(row_name__in=base_disdetail_row_name, version_num=relative_version_num, dis_title=relative_distitle)
        Disdetail.objects.bulk_create([Disdetail(row_name=row_name, row_amt=0, version_num=base_version_num, dis_title=base_distitle) for row_name in base_disdetail_row_name]) # 這裡似乎不會回傳 id 回來
        base_disdetail_qryset_ver2 = Disdetail.objects.filter(row_name__in=base_disdetail_row_name, version_num=base_version_num, dis_title=base_distitle)
        # version 1 disclosure list
        relative_disclosures_list = list(relative_disclosures)
        base_disclosures_list = list(base_disclosures)
        minus_base_disclosures_list = []
        # 比對 基準期 和 另一期
        for b_disdetail in base_disdetail:
            disclosures_in_b_disdetail = list(Disclosure.objects.filter(dis_detail=b_disdetail).values_list('pre__acc_id', flat=True))
            # 基準期的 disclosure 自己先複製一份，version 改為 2，dis detail 對應新建立的基準期 disdetail
            new_b_disclosure = []
            b_amt = 0
            base_disdetail = base_disdetail_qryset_ver2.get(row_name=b_disdetail.row_name)
            for b_disclosure in base_disclosures:
                if b_disclosure.pre.acc_id in disclosures_in_b_disdetail:
                    new_b_disclosure.append(Disclosure(dis_detail=base_disdetail, version_num=base_version_num, pre_amt=b_disclosure.pre_amt, pre=b_disclosure.pre))
                    b_amt += b_disclosure.pre_amt # 計算金額
            # 更新 version 2 的 base disdetail 金額
            base_disdetail.row_amt = b_amt
            base_disdetail.row_amt_in_thou = normal_round(b_amt)
            base_disdetail.save()
            Disclosure.objects.bulk_create(new_b_disclosure)
            # relative 中是否有與 base 相符 disclosure
            relative_disdetail = relative_disdetail_qryset_ver2.get(row_name=b_disdetail.row_name) # 找到與 row name 相同的 relative disdetail
            new_r_disclosure = []
            r_amt = 0
            for r_disclosure in relative_disclosures:
                if r_disclosure.pre.acc_id in disclosures_in_b_disdetail:
                    new_r_disclosure.append(Disclosure(dis_detail=relative_disdetail, version_num=relative_version_num, pre_amt=r_disclosure.pre_amt, pre=r_disclosure.pre))
                    relative_disclosures_list.remove(r_disclosure)
                    minus_base_disclosures_list.append(base_disclosures.get(pre__acc_id=r_disclosure.pre.acc_id))
                    r_amt += r_disclosure.pre_amt # 計算金額
            # 更新 version 2 的 base disdetail 金額
            relative_disdetail.row_amt = r_amt
            relative_disdetail.row_amt_in_thou = normal_round(r_amt)
            relative_disdetail.save()
            Disclosure.objects.bulk_create(new_r_disclosure) # bulk create 不會回傳 id


        # 基準期有但是另一期沒有的 disclosure，最後要讓另一期新增這些 disclosures
        base_disclosures_list = list(set(base_disclosures_list) - set(minus_base_disclosures_list))
        if len(base_disclosures_list) != 0:
            for remaining_b_disclosure in base_disclosures_list:
                Disclosure.objects.create(dis_detail=relative_disdetail_qryset_ver2.get(row_name=remaining_b_disclosure.dis_detail.row_name),
                                          pre_amt=0, version_num=relative_version_num, pre=Preamt.objects.get(acc_id=remaining_b_disclosure.pre.acc_id, rpt_id=relative_rpt))
        # 處理 relative 中沒有被對應到的 disclosures。作法：為兩期分別建立新的 disdetail，每個 disdetail 對應一個剩餘的 disclosure。基準期的沒有的就補 0。
        if len(relative_disclosures_list) != 0:
            for remaining_r_disclosure in relative_disclosures_list:
                # TODO 效率差
                new_b_disdetail = Disdetail.objects.create(row_name=remaining_r_disclosure.pre.acc.acc_name, row_amt=0, dis_title=base_distitle, version_num=base_version_num)
                new_r_disdetail = Disdetail.objects.create(row_name=remaining_r_disclosure.pre.acc.acc_name, row_amt=remaining_r_disclosure.pre_amt, dis_title=relative_distitle, version_num=relative_version_num)
                # 基準期沒有此 disclosure，所以 pre amt = 0
                Disclosure.objects.create(dis_detail=new_b_disdetail, pre=Preamt.objects.get(acc_id=remaining_r_disclosure.pre.acc_id, rpt_id=base_rpt), pre_amt=0, version_num=base_version_num)
                Disclosure.objects.create(dis_detail=new_r_disdetail, pre=remaining_r_disclosure.pre, pre_amt=remaining_r_disclosure.pre_amt, version_num=relative_version_num)
                relative_disclosures_list.remove(remaining_r_disclosure)
        # 組裝回傳結果，預設以前期為準
        return  search_previous_comparision(rpt_id, acc_id, rpt_type, comp_id)
    else:
        return None, None

def search_previous_comparision(rpt_id, acc_id, rpt_type, comp_id):
    '''搜尋目前有無前期比較資料，若有則回傳資料，沒有則回傳 None'''
    current_rpt, previous_rpt = get_current_and_previous_rpt(rpt_id, rpt_type, comp_id)
    if previous_rpt is not None:
        current_disdetails_ver2 = Disdetail.objects.filter(dis_title__rpt=current_rpt, dis_title__dis_name=Account.objects.get(acc_id=acc_id).acc_name, version_num=2)
        previous_disdetails_ver2 = Disdetail.objects.filter(dis_title__rpt=previous_rpt, dis_title__dis_name=Account.objects.get(acc_id=acc_id).acc_name, version_num=3)
        return current_disdetails_ver2, previous_disdetails_ver2
    return None, None

def delete_disdetail_from_previous_comparison(rpt_id, acc_id):
    '''刪除前期比較(version_num為2或3的Disdetail/Disclosure)'''
    disname = Account.objects.filter(acc_id=acc_id).values('acc_name')
    disdetail_qry_set = Disdetail.objects.select_related('rpt__distitle__disdetail').filter(dis_title__rpt_id=rpt_id, dis_title__dis_name=disname[0]['acc_name']).exclude(version_num=1).values()
    if len(disdetail_qry_set) != 0:
        for temp_disdetail in disdetail_qry_set:
            # 因為撈出來的QuerySet裡面是存dict，要先根據dis_detail_id把object撈出來才能做刪除
            disdetail = Disdetail.objects.get(dis_detail_id = temp_disdetail['dis_detail_id'])
            disdetail.delete()
        print('!!!!!delete disdetail from previous comparison successfully.!!!!!')
    else:
        print('!!!!!nothing to delete.!!!!!')