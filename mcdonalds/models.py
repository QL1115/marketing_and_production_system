from django.db import models
from datetime import date
from django.core.validators import MinValueValidator, MaxValueValidator
from model_utils import Choices
from django.utils.translation import ugettext_lazy  as _

##################################### 資料來源為其他部門的 tables
class Sales(models.Model):
    '''行銷相關，資料來源：其他部門。'''
    sales_id = models.AutoField(primary_key=True)
    date = models.DateField() # 只需要其中的 year, month
    numbers = models.PositiveIntegerField() # 數量
    amount = models.PositiveIntegerField() # 金額
    # FK Products, Stores
    product = models.ForeignKey('Products', on_delete=models.CASCADE)
    store = models.ForeignKey('Stores', on_delete=models.CASCADE)
    class Meta:
        db_table = 'sales'

class RFM(models.Model):
    rfm_id = models.SmallAutoField(primary_key=True)
    actual_resp_rate = models.SmallIntegerField(validators=[MaxValueValidator(100)]) # 實際回應率最高 100, 可為負數
    rfm_value = models.PositiveSmallIntegerField()

class Customers(models.Model):
    '''顧客資訊，資料來源：其他部門。'''
    GENDER = Choices(
        (0, 'FEMALE', _('FEMALE')),
        (1, 'MALE', _('MALE'))
    )
    cid = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)
    gender = models.IntegerField(choices = GENDER)
    email = models.EmailField(max_length=30, blank=True, null=True)
    # FK RFM
    rfm = models.ForeignKey('RFM', on_delete=models.CASCADE)

    class Meta:
        db_table = 'customers'

class ShoppingRecords(models.Model):
    '''顧客消費紀錄，資料來源：其他部門'''
    sr_id = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=30) # 商品名稱
    amount = models.PositiveSmallIntegerField() # 消費金額
    shopping_date = models.DateField() # 消費日
    snackes = models.TextField(blank=True) # 配餐，不同名稱用 , 分割
    # FK Customers
    customer = models.ForeignKey('Customers', on_delete=models.CASCADE)

    class Meta:
        db_table = 'shopping_records'

##################################### 屬於我們系統的 tables.
class MarketingStrategies(models.Model):
    '''行銷策略'''
    STRATEGY_STATUS = Choices(
        (0, 'ENABLED', _('ENABLED')),
        (1, 'DISABLED', _('DISABLED'))
    )
    strategy_id = models.AutoField(primary_key=True)
    start_date = models.DateField(default=date.today) # 預設策略開始日期是當天
    end_date = models.DateField()
    status = models.IntegerField(choices=STRATEGY_STATUS, default=STRATEGY_STATUS.ENABLED) # 預設是策略有效
    strategy_name = models.CharField(max_length=30) # 策略名稱
    description = models.TextField(blank=True) # 策略內容，允許為空白

    class Meta:
        ordering = ['status', 'start_date', 'end_date']
        db_table = 'marketing_strategies'


class Products(models.Model):
    '''商品 (eg. 雙層牛肉吉事堡)'''
    product_id = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=30) # 商品名稱
    amount = models.PositiveSmallIntegerField() # 商品售價
    class Meta:
        db_table = 'products'

class RawMaterial(models.Model):
    '''原物料'''
    material_id = models.AutoField(primary_key=True,editable = False)
    material_name = models.CharField(max_length=30) # 原物料名稱
    amount = models.PositiveIntegerField() # 原物料售價
    security_numbers = models.PositiveIntegerField() # 安全存量
    quantity = models.PositiveIntegerField() # 經濟訂購量
    reorder_point = models.PositiveIntegerField() # 再訂購點
    consumption_rate = models.PositiveIntegerField() # 消耗速度：N / 天(期間)
    lead_time = models.PositiveSmallIntegerField() # 前置時間：天數
    expiration_duration = models.PositiveSmallIntegerField() # 有效期間：天數
    on_hand_inventory = models.PositiveIntegerField() # 現有庫存
    # FK Suppliers
    supplier = models.ForeignKey('Suppliers', on_delete=models.CASCADE)
    class Meta:
        db_table = 'raw_material'

class StrategyProductRel(models.Model):
    '''行銷策略與商品之間的關係'''
    spr_id = models.AutoField(primary_key = True)
    numbers = models.PositiveSmallIntegerField() # 此一"行銷策略"下所需的"商品"數
    # FK Products, Strategy
    product = models.ForeignKey('Products', on_delete=models.CASCADE)
    strategy = models.ForeignKey('MarketingStrategies', on_delete=models.CASCADE)
    class Meta:
        db_table = 'strategy_product_rel'

class ProductMaterialRel(models.Model):
    '''商品與原物料之間的關係'''
    pmr_id = models.AutoField(primary_key=True)
    numbers = models.PositiveSmallIntegerField() # 此一"商品"需要多少個這種"原物料"
    # FK Products, RawMaterial
    product = models.ForeignKey('Products', on_delete=models.CASCADE)
    material = models.ForeignKey('RawMaterial', on_delete=models.CASCADE)
    class Meta:
        db_table = 'product_material_rel'

class StoreDemand(models.Model):
    '''門市需求單'''
    DEMAND_STATUS = Choices(
        (0, 'RECEIVED', _('RECEIVED')), # 接收到門市需求單
        (1, 'ARRIVAL', _('ARRIVAL'))   # 原物料已到門市（完成需求單）
    )
    store_demand_id = models.AutoField(primary_key=True)
    created_date = models.DateField(default=date.today)
    status = models.PositiveSmallIntegerField(choices=DEMAND_STATUS, default=DEMAND_STATUS.RECEIVED) # 需求單狀態
    # FK Store
    store = models.ForeignKey('Stores', on_delete=models.CASCADE)

    class Meta:
        ordering = ['created_date', 'status']
        db_table = 'store_demand'

class StoreDemandDetails(models.Model):
    '''門市需求單內容'''
    store_demand_details_id = models.AutoField(primary_key=True)
    prod_numbers = models.PositiveSmallIntegerField() # 所需商品數量
    # FK RawMaterial, Stores
    product = models.ForeignKey('Products', on_delete=models.CASCADE)
    store_demand = models.ForeignKey('StoreDemand', on_delete=models.CASCADE, blank=True, null=True) # TODO 不知道為什麼這裡它要預設值或者要允許 null

    class Meta:
        db_table = 'store_demand_details'

class MarketingData(models.Model):
    '''行銷數據，資料來源：由我們系統算出結果後存入。'''
    md_id = models.AutoField(primary_key=True)
    date = models.DateField() # 只需要其中的 year, month
    cvr = models.PositiveSmallIntegerField(validators=[MinValueValidator(0),
                                                                     MaxValueValidator(100)])
    breakeven_rate = models.PositiveSmallIntegerField(validators=[MinValueValidator(0),
                                                       MaxValueValidator(100)]) # 損益平衡率
    survival_rate = models.PositiveSmallIntegerField(validators=[MinValueValidator(0),
                                                                     MaxValueValidator(100)]) # 存活率
    class Meta:
        db_table = 'marketing_data'

class Suppliers(models.Model):
    '''供應商'''
    supplier_id = models.AutoField(primary_key=True)
    supplier_name = models.CharField(max_length=30) # 供應商名稱
    supplier_address = models.CharField(max_length=255) # 供應商地址
    supplier_phone = models.CharField(max_length=30) # 供應商電話，存成 CharField

    class Meta:
        db_table = 'suppliers'

class Orders(models.Model):
    '''訂單（與上游供應商之間的）'''
    ORDER_STATUS = Choices(
        (0, 'ESTABLISHED', _('ESTABLISHED')), # 建立訂單，已交給上游供應商
        (1, 'ARRIVAL', _('ARRIVAL'))      # 原物料已到配送中心
    )
    order_id = models.AutoField(primary_key=True)
    order_date = models.DateField(default=date.today) # 下訂日期，預設是當天
    status = models.PositiveSmallIntegerField(choices=ORDER_STATUS, default=ORDER_STATUS.ESTABLISHED) # 訂單狀態
    order_amount = models.PositiveIntegerField() # 訂購數量
    # FK RawMaterial
    material = models.ForeignKey('RawMaterial', on_delete=models.CASCADE)

    class Meta:
        ordering = ['order_date', 'status']
        db_table = 'orders'

class Stores(models.Model):
    '''門市'''
    store_id = models.AutoField(primary_key = True)
    store_name = models.CharField(max_length=30) # 門市名稱
    store_address = models.CharField(max_length=255) # 門市地址
    store_phone = models.CharField(max_length=30) # 門市電話，存成 CharField

    class Meta:
        db_table = 'stores'

