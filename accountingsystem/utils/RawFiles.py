from django.core.exceptions import ObjectDoesNotExist
from ..models import Cashinbanks, Depositaccount, Report, Account, Systemcode
from django.db import transaction
from decimal import Decimal, ROUND_05UP
import xlrd # xlrd 方法參考：https://blog.csdn.net/wangweimic/article/details/87344803


def check_and_save_cash_in_banks(rpt_id, sheet): # 參數：sheet 為 Excel 中的分頁
    '''檢查及儲存「銀行存款」'''
    # 1. 檢查 columns 個數，每個 column 的型態(除了 row 1)
    # 2. 一筆一筆存入 CashInBanks table
    # 3. 回傳訊息。

    # 確認有此專案/報表 ID
    rpt = Report.objects.filter(rpt_id=rpt_id).first()  # 如果有就回傳，如果找不到就會回傳 None
    if rpt is None:
        return {"status_code": 404, "msg": "無此專案/報表。"}

    # 確認 column 的名稱和個數是否一致
    expected_ncols = 6
    col_names = ['銀行別', '帳號', '類型', '幣別', '外幣金額', '台幣金額']
    col_types = [xlrd.XL_CELL_TEXT, xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_TEXT, xlrd.XL_CELL_TEXT, xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_NUMBER] # 上傳的檔案欄位長度應該 為 6
    #
    if sheet.ncols != expected_ncols:
        return 422, '檔案欄位個數不符合格式' # '{"status_code": 422, "msg":"檔案欄位個數不符合格式。"}'
    if col_names != sheet.row_values(rowx=0, start_colx=0, end_colx=sheet.nrows): # TODO 之後要更彈性
        return {"status_code": 422, "msg":"檔案欄位名稱不符合格式。"}
    # column 型態檢查，每次檢查一整個 column
    for i in range(expected_ncols):
        # 第 i 個 column 的 cell type，應該會回傳 list
        cell_type_list = sheet.col_types(colx=i, start_rowx=1, end_rowx=sheet.nrows)
        # TODO 處理帳號欄位，如果都是數字，則 xlrd 預設會讀成 NUMBER 的，所以要改成 TEXT 的
        if i == 1: # 「帳號」欄位
            pass
        # TODO index 4 的是外幣金額，index 3 幣別是台幣的，外幣金額可以為 BLANK
        elif i == 4: # 「外幣金額」欄位
            pass
        # 第 i 個 column 的 cell type 應該都是一樣的，並且應該要與 col_types[i] 相同
        elif (cell_type_list[0] != col_types[i]) or (not all(x == cell_type_list[0] for x in cell_type_list)): # 注意寫法
            return {"status_code": 422, "msg": "檔案欄位型態不符合格式。"}

    # 儲存資料：
    try:
        with transaction.atomic():
            for i in range(1, sheet.nrows):
                type = Account.objects.filter(acc_name = sheet.cell_value(rowx=i, colx=2)).first()
                if type is None:
                    raise ObjectDoesNotExist
                record = Cashinbanks.objects.create(bank_name = sheet.cell_value(rowx=i, colx=0),
                                            # 帳號欄位若讀成了「數字」型態，則去掉 .0，否則直接存入 DB
                                           bank_account_number = sheet.cell_value(rowx=i, colx=1) if not isinstance(sheet.cell_value(rowx=i, colx=1), (int, float)) else int(sheet.cell_value(rowx=i, colx=1)),
                                           type = type,
                                           currency = sheet.cell_value(rowx=i, colx=3),
                                           foreign_currency_amount = Decimal(sheet.cell_value(rowx=i, colx=4)).quantize(Decimal('.01'), rounding=ROUND_05UP) if sheet.cell_value(rowx=i, colx=4) != '' else None,
                                           ntd_amount = sheet.cell_value(rowx=i, colx=5),
                                           rpt = rpt)
                record.save()
        return {"status_code": 200, "msg": "檔案上傳/更新成功。"}
    except Exception as e:
        print('check_and_save_cash_in_banks >>> ', e)
        return {"status_code": 500, "msg": "檔案上傳/更新失敗，發生不明錯誤。"}

def check_and_save_deposit_account(rpt_id, sheet): # 參數：sheet 為 Excel 中的分頁
    '''檢查及儲存「定期存款」'''
    # 1. 檢查 columns 個數，每個 column 的型態(除了 row 1)
    # 2. 一筆一筆存入 DepositAccount table
    # 3. 回傳訊息。

    # 確認有此專案/報表 ID
    rpt = Report.objects.filter(rpt_id=rpt_id).first()  # 如果有就回傳，如果找不到就會回傳 None
    if rpt is None:
        return {"status_code": 404, "msg":"無此專案/報表。"}

    # 確認 column 的名稱和個數是否一致
    expected_ncols = 9
    col_names = ['銀行別', '帳號', '類型', '幣別', '外幣金額', '台幣金額', '質押', '開始', '結束']
    col_types = [xlrd.XL_CELL_TEXT, xlrd.XL_CELL_TEXT, xlrd.XL_CELL_TEXT, xlrd.XL_CELL_TEXT, xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_NUMBER
               , xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_DATE, xlrd.XL_CELL_DATE] # 上傳的檔案欄位長度應該 為 9
    #
    if sheet.ncols != expected_ncols:
        return {"status_code": 422, "msg":"檔案欄位個數不符合格式。"}
    if col_names != sheet.row_values(rowx=0, start_colx=0, end_colx=sheet.nrows): # TODO 之後要更彈性
        return {"status_code": 422, "msg":"檔案欄位名稱不符合格式。"}
    # column 型態檢查，每次檢查一整個 column
    for i in range(expected_ncols):
        # 第 i 個 column 的 cell type，應該會回傳 list
        cell_type_list = sheet.col_types(colx=i, start_rowx=1, end_rowx=sheet.nrows)
        # TODO 處理帳號欄位，如果都是數字，則 xlrd 預設會讀成 NUMBER 的，所以要改成 TEXT 的
        if i == 1:
            pass
        # TODO index 4 的是外幣金額，index 3 幣別是台幣的，外幣金額可以為 BLANK
        elif i == 4:  # and  sheet.cell_value(rowx=1, colx=3) == '台幣':
            pass
        # 第 i 個 column 的 cell type 應該都是一樣的，並且應該要與 col_types[i] 相同
        elif (cell_type_list[0] != col_types[i]) or (not all(x == cell_type_list[0] for x in cell_type_list)): # 注意寫法
            return {"status_code": 422, "msg":"檔案欄位型態不符合格式。"}

    # 儲存資料：
    try:
        with transaction.atomic():
            for i in range(1, sheet.nrows):
                # row_values = sheet.row_values(i, )
                type = Account.objects.filter(acc_name = sheet.cell_value(rowx=i, colx=2)).first()
                currency = Systemcode.objects.filter(code_type='幣別', code_name=sheet.cell_value(rowx=i, colx=2)).first().system_code # currency欄位存所屬幣別的system_code
                if type is None:
                    raise ObjectDoesNotExist
                if currency is None:
                    raise ObjectDoesNotExist
                record = Depositaccount.objects.create(
                                                     bank_name = sheet.cell_value(rowx=i, colx=0),
                                                     bank_account_number = sheet.cell_value(rowx=i, colx=1) if not isinstance(sheet.cell_value(rowx=i, colx=1), (int, float)) else int(sheet.cell_value(rowx=i, colx=1)),
                                                     type = type,
                                                     currency = currency,
                                                     foreign_currency_amount = Decimal(sheet.cell_value(rowx=i, colx=4)).quantize(Decimal('.01'), rounding=ROUND_05UP) if sheet.cell_value(rowx=i, colx=4) != '' else None,
                                                     ntd_amount = sheet.cell_value(rowx=i, colx=5),
                                                     plege = sheet.cell_value(rowx=i, colx=6),
                                                     start_date = sheet.cell_value(rowx=i, colx=7),
                                                     end_date = sheet.cell_value(rowx=i, colx=8),
                                                     rpt = rpt)
                record.save()
        return {"status_code": 200, "msg": "檔案上傳/更新成功。"}
    except Exception as e:
        print('check_and_save_cah_in_banks >>> ', e)
        return {"status_code": 500, "msg": "檔案上傳/更新失敗，發生不明錯誤。"}

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

def get_uploaded_file(rpt_id, table_name):
    '''根據 table name 抓取特定的上傳資料。eg. cash_in_banks 代表銀行存款'''
    # how to use: get_uploaded_file(rpt_id, table_name).get('returnObject')
    # 使用須知: 回傳的depositaccount object內的type欄位是存Account object, 呈現時需轉換成科目名稱 (type.name)
    #                                          currency欄位是存幣別代碼, 呈現時需轉換成幣別名稱 (Systemcode.objects.filter(code_type='幣別', system_code=currency).first().code_name)
    # 1. 根據 rpt_id 和table_name 抓取指定 uploaded file
	# 2. 使用filter(rpt_id)抓取資料，回傳整個QuerySet
    # 3. 回傳訊息。無資料：告知使用者資料庫無此筆資料。失敗：告知使用者發生不明錯誤。
    try:
        report = Report.objects.filter(rpt_id=rpt_id)[0]
        returnDict = {}
        if table_name == 'cash_in_banks': # 銀行存款
            returnObject = Cashinbanks.objects.filter(rpt=report)
            if len(returnObject) != 0:
                returnDict = {"status_code":200, "returnObject": returnObject} # 因為TABLE會含有多個row, 直接回傳整個QuerySet
            else:
                
                returnDict = {"status_code":404, "msg": "資料庫無此筆資料。"}
                
        elif table_name == 'deposit_account': # 定期存款
            returnObject = Depositaccount.objects.filter(rpt=report)
            if len(returnObject) != 0:
                returnDict = {"status_code":200, "returnObject": returnObject} # 因為TABLE會含有多個row, 直接回傳整個QuerySet
            else:
                returnDict = {"status_code":404, "msg": "資料庫無此筆資料。"}
        return returnDict
    except Exception as e:
        print('get_uploaded_file >>> ', e)
        return {"status_code":500, "msg": "發生不明錯誤。"}
