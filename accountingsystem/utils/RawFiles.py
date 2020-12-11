from django.core.exceptions import ObjectDoesNotExist

from ..models import Cashinbanks, Depositaccount, Report, Account
import xlrd # xlrd 方法參考：https://blog.csdn.net/wangweimic/article/details/87344803
from django.db import transaction



def check_and_save_cash_in_banks(rpt_id, sheet): # 參數：sheet 為 Excel 中的分頁
    '''檢查及儲存「銀行存款」'''
    # 1. 檢查 columns 個數，每個 column 的型態(除了 row 1)
    # 2. 一筆一筆存入 CashInBanks table
    # 3. 回傳訊息。

    # 確認有此專案/報表 ID
    rpt = Report.objects.filter(rpt_id=rpt_id).first()  # 如果有就回傳，如果找不到就會回傳 None
    if rpt is None:
        return '{"status_code": 404, "msg":"無此專案/報表。"}'

    # 確認 column 的名稱和個數是否一致
    expected_ncols = 6
    col_names = ['銀行別', '帳號', '類型', '幣別', '外幣金額', '台幣金額']
    col_types = [xlrd.XL_CELL_TEXT, xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_TEXT, xlrd.XL_CELL_TEXT, xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_NUMBER] # 上傳的檔案欄位長度應該 為 6
    #
    if sheet.ncols != expected_ncols:
        return '{"status_code": 422, "msg":"檔案欄位個數不符合格式。"}'
    if col_names != sheet.row_values(rowx=0, start_colx=0, end_colx=sheet.nrows): # TODO 之後要更彈性
        return '{"status_code": 422, "msg":"檔案欄位名稱不符合格式。"}'
    # column 型態檢查，每次檢查一整個 column
    for i in range(expected_ncols):
        # 第 i 個 column 的 cell type，應該會回傳 list
        cell_type_list = sheet.col_types(colx=i, start_rowx=1, end_rowx=sheet.nrows)
        # 第 i 個 column 的 cell type 應該都是一樣的，並且應該要與 col_types[i] 相同
        if (cell_type_list[0] != col_types[i]) or (not all(x == cell_type_list[0] for x in cell_type_list)): # 注意寫法
            return '{"status_code": 422, "msg":"檔案欄位名稱不符合格式。"}'

    # 儲存資料：
    try:
        with transaction.atomic():
            for i in range(1, sheet.nrows):
                # row_values = sheet.row_values(i, )
                type = Account.objects.filter(acc_name = sheet.cell_value(rowx=i, colx=2)).first()
                if type is None:
                    raise ObjectDoesNotExist
                record = Cashinbanks.objects.create(bank_name = sheet.cell_value(rowx=i, colx=0),
                                           bank_account_number = str(sheet.cell_value(rowx=i, colx=1)), # TODO 可能遺失左邊的 0
                                           type = type,
                                           currency = sheet.cell_value(rowx=i, colx=3),
                                           foreign_currency_amount = sheet.cell_value(rowx=i, colx=4),
                                           ntd_amount = sheet.cell_value(rowx=i, colx=5),
                                           rpt = rpt)
                record.save(commit=True)
        return '{"status_code": 200, "msg": "檔案上傳/更新成功。"}'
    except Exception as e:
        print('check_and_save_cah_in_banks >>> ', e)
        return '{"status_code": 500, "msg": "檔案上傳/更新失敗，發生不明錯誤。"}'


def delete_uploaded_file(rpt_id, table_name):
    '''根據 table name 刪除特定的上傳資料。eg. cash_in_banks 代表銀行存款'''
    # 1. 根據 rpt_id 和 table_name 判斷要刪除那個 uploaded file
    # 2. 刪除對應 rows。
    # 3. 回傳訊息。成功：告知使用者刪除的是哪個 rpt id 的哪一個上傳檔案。失敗：告知使用者發生不明錯誤。
    try:
        report = Report.objects.filter(rpt_id=rpt_id)[0]
        if table_name == 'cash_in_banks': # 銀行存款
            Cashinbanks.objects.filter(rpt=report).delete()
        elif table_name == 'deposit_account': # 定期存款
            Depositaccount.objects.filter(rpt=report).delete()
        return '{"status_code":200, "msg": "您刪除了 id 為' + str(report.id) + ' 專案的' + table_name +'。"}'
    except Exception as e:
        print('delete_uploaded_file >>> ', e)
        return '{"status_code":500, "msg": "刪除資料發生不明錯誤。}'
