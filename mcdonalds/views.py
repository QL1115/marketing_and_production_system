from django.shortcuts import render
from django.http import HttpResponse

# from mcdonalds.forms import RawMaterialModelForm
from .forms import MarketingStrategyForm
from .models import Sales, RFM, Customers, ShoppingRecords, MarketingStrategies, Products, RawMaterial, StrategyProductRel, ProductMaterialRel, StoreDemand, StoreDemandDetails, MarketingData, Stores, Orders, Suppliers
from django.db import connection

# Create your views here.
def index(request):
    return render(request, 'mcdonalds/index.html', {})

def stores_detail(request):
    stores=Stores.objects.values()
    return render(request,'mcdonalds/stores_detail.html', {'stores': stores})

def raw_materials_predict(request):
    raw_materials_predict=RawMaterial.objects.values('material_name', 'quantity', 'reorder_point').order_by('reorder_point')
    print(raw_materials_predict)
    return render(request,'mcdonalds/raw_material_predict.html', {'raw_materials_predict': raw_materials_predict})

def raw_materials_order(request):
    # raw_materials_order=Orders.objects.all()
    # raw_materials_order=Orders.objects.values('status', 'order_amount', 'reorder_point')
    # raw_materials_order=Orders.objects.all().select_related('material_name','order_amount','status','order_date')
    # raw_materials_order=Orders.objects.all().prefetch_related('material').values('material_name','order_amount','status','order_date')\
    # #>>> raw_materials_order=Orders.objects.values('order_id','order_amount','status','order_date').filter(order_id=1)
    cursor2 = connection.cursor()   
    cursor2.execute("SELECT material_name, order_amount, order_date, status FROM orders INNER JOIN raw_material ON orders.material_id=raw_material.material_id;")
    raw_materials_order = dictfetchall(cursor2)

    for i in raw_materials_order:
        if i['status']==0:
            i['status']='未完成'
            print(i['status'])
        else:
            i['status']='已完成'
    return render(request,'mcdonalds/raw_materials_order.html', {'raw_materials_order': raw_materials_order})

def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def raw_materials(request):
    cursor = connection.cursor()   
    cursor.execute("SELECT material_id,material_name, amount, on_hand_inventory, security_numbers,supplier_name FROM raw_material INNER JOIN suppliers ON raw_material.supplier_id=suppliers.supplier_id;")
    raw_materials = dictfetchall(cursor)
    return render(request,'mcdonalds/raw_material.html', {'raw_materials': raw_materials})



def update_raw_materials(request, pk):
    raw_materials = RawMaterial.objects.get(material_id=pk)

    form = RawMaterialModelForm(instance=raw_materials)
    context = {
        'form': form
    }
    return render(request, 'expenses/update_raw_materials.html', context)

def strategies_list(request):
    '''行銷策略列表'''

    context = {

    }
    return render(request, 'mcdonalds/marketing_strategies_list.html', context)

def strategies_detail(request, pk):
    '''行銷策略詳細資訊'''
    context = {'strategy_id': pk}
    if request.method == 'GET':
        form = MarketingStrategyForm()
        context['form'] = form
    elif request.method == 'POST':
        context['msg'] = '上傳成功與否資訊' # TODO 之後要修改
    return render(request, 'mcdonalds/marketing_strategies_detail.html', context)

def binary_tree(request):
    '''二元樹'''
    context = {

    }
    return render(request, 'mcdonalds/binary_tree.html', context)


