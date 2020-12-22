from django.shortcuts import render,redirect
from django.http import HttpResponse
from .models import Sales, RFM, Customers, ShoppingRecords, MarketingStrategies, Products, RawMaterial, StrategyProductRel, ProductMaterialRel, StoreDemand, StoreDemandDetails, MarketingData, Stores, Orders, Suppliers
from django.db import connection
from .forms import RawMaterialModelForm 

# Create your views here.
def index(request):
    return HttpResponse('產銷資訊系統首頁')

def stores_contact(request):
    stores=Stores.objects.values()
    return render(request,'mcdonalds/stores_contact.html', {'stores': stores})

def suppliers_contact(request):
    suppliers=Suppliers.objects.values()
    return render(request,'mcdonalds/suppliers_contact.html', {'suppliers': suppliers})

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



def update_raw_materials(request,id):
    raw_materials = RawMaterial.objects.get(id=id)
    print(id)
    form = RawMaterialModelForm(instance=raw_materials)
    context = {
        'form': form
    }
    return render(request, 'expenses/update_raw_materials.html', context)

def get_edit_page(request, material_id):  
    raw_materials = RawMaterial.objects.get(material_id=material_id)  
    print('!')
    print(raw_materials.material_id)

    return render(request,'mcdonalds/update_raw_materials.html', {'raw_materials':raw_materials}) 


def save_update(request, material_id):  
    raw_materials = RawMaterial.objects.get(material_id=material_id)  
    form = RawMaterialModelForm(request.POST, instance = raw_materials)  
    print('here~~~~~~')
    if form.is_valid():  
        form.save()  
        return redirect("/mcdonalds/raw_materials")  
    return render(request, 'mcdonalds/update_raw_materials.html', {'raw_materials': raw_materials}) 


 
