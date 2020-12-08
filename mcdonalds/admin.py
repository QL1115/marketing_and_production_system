from django.contrib import admin
from .models import Sales, RFM, Customers, ShoppingRecords, MarketingStrategies, Products, RawMaterial, StrategyProductRel, ProductMaterialRel, StoreDemand, StoreDemandDetails, MarketingData, Stores, Orders, Suppliers


# Register your models here.
admin.register(Sales)
admin.register(RFM)
admin.register(Customers)
admin.register(ShoppingRecords)
admin.register(MarketingStrategies)
admin.register(Products)
admin.register(RawMaterial)
admin.register(StrategyProductRel)
admin.register(ProductMaterialRel)
admin.register(StoreDemand)
admin.register(StoreDemandDetails)
admin.register(MarketingData)
admin.register(Stores)
admin.register(Orders)
admin.register(Suppliers)
