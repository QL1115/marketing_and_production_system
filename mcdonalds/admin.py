from django.contrib import admin
from .models import Sales, RFM, Customers, ShoppingRecords, MarketingStrategies, Products, RawMaterial, StrategyProductRel, ProductMaterialRel, StoreDemand, StoreDemandDetails, MarketingData, Stores, Orders, Suppliers


# Register your models here.
admin.site.register(Sales)
admin.site.register(RFM)
admin.site.register(Customers)
admin.site.register(ShoppingRecords)
admin.site.register(MarketingStrategies)
admin.site.register(Products)
admin.site.register(RawMaterial)
admin.site.register(StrategyProductRel)
admin.site.register(ProductMaterialRel)
admin.site.register(StoreDemand)
admin.site.register(StoreDemandDetails)
admin.site.register(MarketingData)
admin.site.register(Stores)
admin.site.register(Orders)
admin.site.register(Suppliers)
