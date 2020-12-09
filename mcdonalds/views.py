from django.shortcuts import render
from django.http import HttpResponse
from .models import Sales, RFM, Customers, ShoppingRecords, MarketingStrategies, Products, RawMaterial, StrategyProductRel, ProductMaterialRel, StoreDemand, StoreDemandDetails, MarketingData, Stores, Orders, Suppliers

# Create your views here.
def index(request):
    return HttpResponse('產銷資訊系統首頁')

def stores_detail(request):
    stores=Stores.objects.values()
    return render(request,'mcdonalds/stores_detail.html', {'stores': stores})

