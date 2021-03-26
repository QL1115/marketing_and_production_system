from django.core.exceptions import ObjectDoesNotExist
from ..models import Cashinbanks, Depositaccount, Report, Account, Systemcode, ReceiptsInAdvance, Accountreceivable, Allowanceforloss
from django.db import transaction
from decimal import Decimal, ROUND_05UP
from datetime import datetime
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
    col_names = ['銀行別', '帳號', '類型', '幣別', '外幣金額', '原幣金額']
    col_types = [xlrd.XL_CELL_TEXT, xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_TEXT, xlrd.XL_CELL_TEXT, xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_NUMBER] # 上傳的檔案欄位長度應該 為 6
    #
    if sheet.ncols != expected_ncols:
        return  {"status_code": 422, "msg":"檔案欄位個數不符合格式。"}
    if col_names != sheet.row_values(rowx=0, start_colx=0, end_colx=sheet.ncols): # TODO 之後要更彈性
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
                currency = Systemcode.objects.filter(code_type='幣別', code_name=sheet.cell_value(rowx=i,
                                                                                                colx=3)).first().system_code  # currency欄位存所屬幣別的system_code
                if type is None:
                    raise ObjectDoesNotExist
                if currency is None:
                    raise ObjectDoesNotExist
                if type is None:
                    raise ObjectDoesNotExist
                record = Cashinbanks.objects.create(bank_name = sheet.cell_value(rowx=i, colx=0),
                                            # 帳號欄位若讀成了「數字」型態，則去掉 .0，否則直接存入 DB
                                           bank_account_number = sheet.cell_value(rowx=i, colx=1) if not isinstance(sheet.cell_value(rowx=i, colx=1), (int, float)) else int(sheet.cell_value(rowx=i, colx=1)),
                                           type = type,
                                           currency = currency,
                                           foreign_currency_amount = Decimal(sheet.cell_value(rowx=i, colx=4)).quantize(Decimal('.01'), rounding=ROUND_05UP) if sheet.cell_value(rowx=i, colx=4) != '' else None,
                                           ntd_amount = Decimal(sheet.cell_value(rowx=i, colx=5)).quantize(Decimal('.01'), rounding=ROUND_05UP),
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
    col_names = ['銀行別', '帳號', '類型', '幣別', '外幣金額', '原幣金額', '質押', '開始', '結束']
    col_types = [xlrd.XL_CELL_TEXT, xlrd.XL_CELL_TEXT, xlrd.XL_CELL_TEXT, xlrd.XL_CELL_TEXT, xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_NUMBER
               , xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_DATE, xlrd.XL_CELL_DATE] # 上傳的檔案欄位長度應該 為 9
    #
    print('input 表 ', sheet.row_values(rowx=0, start_colx=0, end_colx=sheet.ncols))
    if sheet.ncols != expected_ncols:
        return {"status_code": 422, "msg":"檔案欄位個數不符合格式。"}
    if col_names != sheet.row_values(rowx=0, start_colx=0, end_colx=sheet.ncols): # TODO 之後要更彈性
        print('名稱？？')
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
                currency = Systemcode.objects.filter(code_type='幣別', code_name=sheet.cell_value(rowx=i, colx=3)).first().system_code # currency欄位存所屬幣別的system_code
                if type is None:
                    raise ObjectDoesNotExist
                if currency is None:
                    raise ObjectDoesNotExist
                record = Depositaccount.objects.create(
                                                     bank_name = sheet.cell_value(rowx=i, colx=0),
                                                     # 帳號欄位若讀成了「數字」型態，則去掉 .0，否則直接存入 DB
                                                     bank_account_number = sheet.cell_value(rowx=i, colx=1) if not isinstance(sheet.cell_value(rowx=i, colx=1), (int, float)) else int(sheet.cell_value(rowx=i, colx=1)),
                                                     type = type,
                                                     currency = currency,
                                                     foreign_currency_amount = Decimal(sheet.cell_value(rowx=i, colx=4)).quantize(Decimal('.01'), rounding=ROUND_05UP) if sheet.cell_value(rowx=i, colx=4) != '' else None,
                                                     ntd_amount = Decimal(sheet.cell_value(rowx=i, colx=5)).quantize(Decimal('.01'), rounding=ROUND_05UP),
                                                     plege = sheet.cell_value(rowx=i, colx=6),
                                                     # xlrd直接讀日期會是float，需轉成datetime後存入DB
                                                     start_date = datetime(*xlrd.xldate_as_tuple(sheet.cell_value(rowx=i, colx=7), 0)), 
                                                     end_date = datetime(*xlrd.xldate_as_tuple(sheet.cell_value(rowx=i, colx=8), 0)),
                                                     rpt = rpt)
                record.save()

        return {"status_code": 200, "msg": "檔案上傳/更新成功。"}
    except Exception as e:
        print('check_and_save_deposit_account >>> ', e)
        return {"status_code": 500, "msg": "檔案上傳/更新失敗，發生不明錯誤。"}

def check_and_save_receipts_in_advance(rpt_id, sheet):
    ''' 檢查及儲存「預收款項」 '''
    # 確認有此專案/報表 ID
    rpt = Report.objects.filter(rpt_id=rpt_id).first()  # 如果有就回傳，如果找不到就會回傳 None
    if rpt is None:
        return {"status_code": 404, "msg": "無此專案/報表。"}
    # 確認 column 的名稱和個數是否一致
    col_names = ['傳票編號', '傳票日期', '客戶代號', '客戶簡稱', '幣別', '外幣金額', '原幣金額', '摘要']
    col_types = [xlrd.XL_CELL_TEXT, xlrd.XL_CELL_DATE, xlrd.XL_CELL_TEXT, xlrd.XL_CELL_TEXT, xlrd.XL_CELL_TEXT, xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_TEXT] 
    expected_ncols = len(col_names)
    #
    if sheet.ncols != expected_ncols:
        return {"status_code": 422, "msg":"檔案欄位個數不符合格式。"}
    if col_names != sheet.row_values(rowx=0, start_colx=0, end_colx=sheet.nrows): # TODO 之後要更彈性
        return {"status_code": 422, "msg":"檔案欄位名稱不符合格式。"}
    # column 型態檢查，每次檢查一整個 column
    for i in range(expected_ncols):
        # 第 i 個 column 的 cell type，應該會回傳 list
        cell_type_list = sheet.col_types(colx=i, start_rowx=1, end_rowx=sheet.nrows)
        if i == 0: # TODO 傳票編號欄位，如果都是數字，則 xlrd 預設會讀成 NUMBER 的，所以要改成 TEXT 的
            pass
        elif i == 3: # 客戶簡稱欄位
            pass
        elif i == 5: # 外幣金額欄位: 有可能是空白或數字
            temp = [el for el in cell_type_list if el != col_types[i]]
            # if not all(x == (col_types[i] or xlrd.XL_CELL_EMPTY) for x in cell_type_list):
            if not all(x == xlrd.XL_CELL_EMPTY for x in temp):
                return {"status_code": 422, "msg": "外幣金額欄位不符合格式。"}
        # 第 i 個 column 的 cell type 應該都是一樣的，並且應該要與 col_types[i] 相同
        elif (cell_type_list[0] != col_types[i]) or (not all(x == cell_type_list[0] for x in cell_type_list)): # 注意寫法
            print('cell_type_list >>> ', cell_type_list)
            return {"status_code": 422, "msg": "檔案欄位型態不符合格式。"}

    # 儲存資料：
    try:
        with transaction.atomic():
            receipts_in_advance_list = [] # 儲存多個欲新增至資料庫的預收款項 obj
            for i in range(1, sheet.nrows):
                currency = Systemcode.objects.filter(code_type='幣別', code_name=sheet.cell_value(rowx=i, colx=4)).first().system_code  # currency欄位存所屬幣別的system_code
                if currency is None:
                    raise ObjectDoesNotExist
                receipts_in_advance_list.append(ReceiptsInAdvance(
                                                        voucher_num=sheet.cell_value(rowx=i, colx=0) if not isinstance(sheet.cell_value(rowx=i, colx=0), (int, float)) else int(sheet.cell_value(rowx=i, colx=0)),
                                                        voucher_date=datetime(*xlrd.xldate_as_tuple(sheet.cell_value(rowx=i, colx=1), 0)),
                                                        customer_code=sheet.cell_value(rowx=i, colx=2) if not isinstance(sheet.cell_value(rowx=i, colx=2), (int, float)) else int(sheet.cell_value(rowx=i, colx=2)),
                                                        customer_abbre=sheet.cell_value(rowx=i, colx=3),
                                                        currency=currency,
                                                        foreign_currency_amount=Decimal(sheet.cell_value(rowx=i, colx=5)).quantize(Decimal('.01'), rounding=ROUND_05UP) if sheet.cell_value(rowx=i, colx=5) != '' else None,
                                                        ntd_amount=Decimal(sheet.cell_value(rowx=i, colx=6)).quantize(Decimal('.01'), rounding=ROUND_05UP),
                                                        summary=sheet.cell_value(rowx=i, colx=7),
                                                        rpt=rpt))
            # 一次新增至資料庫中
            ReceiptsInAdvance.objects.bulk_create(receipts_in_advance_list)
        return {"status_code": 200, "msg": "檔案上傳/更新成功。"}
    except Exception as e:
        print('check_and_save_cash_in_banks >>> ', e)
        return {"status_code": 500, "msg": "檔案上傳/更新失敗，請檢查 Excel 格式及內容。"}

def check_and_save_accountreceivable(rpt_id, sheet):
    ''' 檢查及儲存「應收帳款」 '''
    # 確認有此專案/報表 ID
    rpt = Report.objects.filter(rpt_id=rpt_id).first()  # 如果有就回傳，如果找不到就會回傳 None
    if rpt is None:
        return {"status_code": 404, "msg": "無此專案/報表。"}
    # 確認 column 的名稱和個數是否一致
    col_names = ['傳票編號', '傳票日期', '客戶代號', '客戶簡稱', '幣別', '外幣金額', '本幣金額', '摘要', '預計收款日']
    col_types = [xlrd.XL_CELL_TEXT, xlrd.XL_CELL_DATE, xlrd.XL_CELL_TEXT, xlrd.XL_CELL_TEXT, xlrd.XL_CELL_TEXT, xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_TEXT, xlrd.XL_CELL_DATE]
    expected_ncols = len(col_names)
    #
    if sheet.ncols != expected_ncols:
        return {"status_code": 422, "msg":"檔案欄位個數不符合格式。"}
    if col_names != sheet.row_values(rowx=0, start_colx=0, end_colx=sheet.nrows): # TODO 之後要更彈性
        return {"status_code": 422, "msg":"檔案欄位名稱不符合格式。"}
    # column 型態檢查，每次檢查一整個 column
    """for i in range(expected_ncols):
        # 第 i 個 column 的 cell type，應該會回傳 list
        print('col_value >>>', sheet.col_values(colx=i, start_rowx=1, end_rowx=sheet.nrows))
        cell_type_list = sheet.col_types(colx=i, start_rowx=1, end_rowx=sheet.nrows)
        # 第 i 個 column 的 cell type 應該都是一樣的，並且應該要與 col_types[i] 相同
        if (cell_type_list[0] != col_types[i]) or (not all(x == cell_type_list[0] for x in cell_type_list)): # 注意寫法
            print('cell_type_list >>> ', cell_type_list)
            return {"status_code": 422, "msg": "檔案欄位型態不符合格式。"}"""

    # 儲存資料：
    try:
        with transaction.atomic():
            account_receivable_list = [] # 儲存多個欲新增至資料庫的預收款項 obj
            for i in range(1, sheet.nrows):
                currency = Systemcode.objects.filter(code_type='幣別', code_name=sheet.cell_value(rowx=i, colx=4)).first().system_code  # currency欄位存所屬幣別的system_code
                if currency is None:
                    raise ObjectDoesNotExist
                account_receivable_list.append(Accountreceivable(
                                                        voucher_num=sheet.cell_value(rowx=i, colx=0) if not isinstance(sheet.cell_value(rowx=i, colx=0), (int, float)) else int(sheet.cell_value(rowx=i, colx=0)),
                                                        voucher_date=datetime(*xlrd.xldate_as_tuple(sheet.cell_value(rowx=i, colx=1), 0)),
                                                        customer_code=sheet.cell_value(rowx=i, colx=2) if not isinstance(sheet.cell_value(rowx=i, colx=2), (int, float)) else int(sheet.cell_value(rowx=i, colx=2)),
                                                        customer_abbre=sheet.cell_value(rowx=i, colx=3),
                                                        currency=currency,
                                                        foreign_currency_amount=Decimal(sheet.cell_value(rowx=i, colx=5)).quantize(Decimal('.01'), rounding=ROUND_05UP) if sheet.cell_value(rowx=i, colx=5) != '' else None,
                                                        ntd_amount=Decimal(sheet.cell_value(rowx=i, colx=6)).quantize(Decimal('.01'), rounding=ROUND_05UP),
                                                        summary=sheet.cell_value(rowx=i, colx=7),
                                                        est_payment_date=datetime(*xlrd.xldate_as_tuple(sheet.cell_value(rowx=i, colx=8), 0)),
                                                        rpt=rpt))
            # 一次新增至資料庫中
            Accountreceivable.objects.bulk_create(account_receivable_list)
        return {"status_code": 200, "msg": "檔案上傳/更新成功。"}
    except Exception as e:
        print('check_and_save_accountreceivable >>> ', e)
        return {"status_code": 500, "msg": "檔案上傳/更新失敗，請檢查 Excel 格式及內容。"}

def check_and_save_allowanceforloss(rpt_id, sheet):
    ''' 檢查及儲存「備抵損失」 '''
    # 確認有此專案/報表 ID
    rpt = Report.objects.filter(rpt_id=rpt_id).first()  # 如果有就回傳，如果找不到就會回傳 None
    if rpt is None:
        return {"status_code": 404, "msg": "無此專案/報表。"}
    # 確認 row 的名稱和個數是否一致
    row_names = ['期初餘額', '本期提列', '減損迴轉', '無法收回而沖銷', '兌換損益', '備抵損失-非關係人', '備抵損失-關係人']
    row_types = [xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_NUMBER]
    expected_nrows = len(row_names)
    #
    if sheet.ncols != expected_nrows:
        return {"status_code": 422, "msg":"檔案欄位個數不符合格式。"}
    if row_names != sheet.col_values(colx=0, start_rowx=0, end_rowx=sheet.ncols): # TODO 之後要更彈性
        return {"status_code": 422, "msg":"檔案欄位名稱不符合格式。"}
    # row 型態檢查，每次檢查一整個 row
    for i in range(expected_nrows):
        # 第 i 個 row 的 cell type，應該會回傳 list
        cell_type_list = sheet.row_types(rowx=i, start_colx=1, end_colx=sheet.ncols)
        if i == 5: # 外幣金額欄位: 有可能是空白或數字
            temp = [el for el in cell_type_list if el != row_types[i]]
            # if not all(x == (col_types[i] or xlrd.XL_CELL_EMPTY) for x in cell_type_list):
            if not all(x == xlrd.XL_CELL_EMPTY for x in temp):
                return {"status_code": 422, "msg": "金額欄位不符合格式。"}
        # 第 i 個 row 的 cell type 應該都是一樣的，並且應該要與 row_types[i] 相同
        elif (cell_type_list[0] != row_types[i]) or (not all(x == cell_type_list[0] for x in cell_type_list)): # 注意寫法
            print('cell_type_list >>> ', cell_type_list)
            return {"status_code": 422, "msg": "檔案欄位型態不符合格式。"}

    # 儲存資料：
    try:
        with transaction.atomic():
            allowence_for_loss_list = [] # 儲存多個欲新增至資料庫的預收款項 obj
            for i in range(1, sheet.ncols):
                currency = Systemcode.objects.filter(code_type='幣別', code_name=sheet.cell_value(rowx=i, colx=4)).first().system_code  # currency欄位存所屬幣別的system_code
                if currency is None:
                    raise ObjectDoesNotExist
                allowence_for_loss_list.append(Allowanceforloss(
                                                        opening_balance=Decimal(sheet.cell_value(rowx=1, colx=i)).quantize(Decimal('.01'), rounding=ROUND_05UP),
                                                        recognized_amt=Decimal(sheet.cell_value(rowx=2, colx=i)).quantize(Decimal('.01'), rounding=ROUND_05UP),
                                                        reversal_amt=Decimal(sheet.cell_value(rowx=3, colx=i)).quantize(Decimal('.01'), rounding=ROUND_05UP),
                                                        charge_off_amt=Decimal(sheet.cell_value(rowx=4, colx=i)).quantize(Decimal('.01'), rounding=ROUND_05UP),
                                                        exchange_gain_loss=Decimal(sheet.cell_value(rowx=5, colx=i)).quantize(Decimal('.01'), rounding=ROUND_05UP),
                                                        alw_for_loss_individual=Decimal(sheet.cell_value(rowx=6, colx=i)).quantize(Decimal('.01'), rounding=ROUND_05UP),
                                                        alw_for_loss_consolidate=Decimal(sheet.cell_value(rowx=7, colx=i)).quantize(Decimal('.01'), rounding=ROUND_05UP),
                                                        rpt=rpt))
            # 一次新增至資料庫中
            ReceiptsInAdvance.objects.bulk_create(allowence_for_loss_list)
        return {"status_code": 200, "msg": "檔案上傳/更新成功。"}
    except Exception as e:
        print('check_and_save_accountreceivable >>> ', e)
        return {"status_code": 500, "msg": "檔案上傳/更新失敗，請檢查 Excel 格式及內容。"}

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
        elif table_name == 'receipts_in_advance':
            print('in delete 27')
            ReceiptsInAdvance.objects.filter(rpt=report).delete()
        elif table_name == 'account_receivable':
            print('in delete 3')
            Accountreceivable.objects.filter(rpt=report).delete()
        elif table_name == 'allowance_for_loss':
            print('in delete 35')
            Allowanceforloss.objects.filter(rpt=report).delete()
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