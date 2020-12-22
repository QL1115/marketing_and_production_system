from django.shortcuts import render,redirect
from django.http import HttpResponse
from plotly.graph_objs import Scatter
from plotly.offline import plot

from .models import Sales, RFM, Customers, ShoppingRecords, MarketingStrategies, Products, RawMaterial, StrategyProductRel, ProductMaterialRel, StoreDemand, StoreDemandDetails, MarketingData, Stores, Orders, Suppliers
from django.db import connection
from .forms import RawMaterialModelForm, MarketingStrategyForm
import plotly.graph_objects as go
import pandas as pd

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



def update_raw_materials(request,id):
    raw_materials = RawMaterial.objects.get(id=id)
    print(id)
    form = RawMaterialModelForm(instance=raw_materials)
    context = {
        'form': form
    }
    return render(request, 'expenses/update_raw_materials.html', context)

def strategies_list(request):
    '''行銷策略列表'''

    strategies_list = MarketingStrategies.objects.all()
    context = {
        'strategies_list': strategies_list
    }
    return render(request, 'mcdonalds/marketing_strategies_list.html', context)

def add_strategy(request):
    '''新增行銷策略'''
    if request.method == 'POST':
        form = MarketingStrategyForm(request.POST)
        if form.is_valid():
            new_strategy = form.save()
            print('new_strategy >>> ', new_strategy)
            # return redirect('/mcdonalds/strategy/update/' + str(new_strategy.strategy_id) + '/')
            return render(request, 'mcdonalds/marketing_strategies_detail.html', {'form': form, 'isAdded':True})
    else:
        form = MarketingStrategyForm()
        return render(request, 'mcdonalds/marketing_strategies_detail.html', {'form': form})

def update_strategy(request, strategy_id):
    '''查看及修改行銷策略詳細資訊'''
    if request.method == 'POST':
        form = MarketingStrategyForm(request.POST)
        if form.is_valid():
            strategy = MarketingStrategies.objects.get(pk=strategy_id)
            form = MarketingStrategyForm(request.POST, instance=strategy)
            updated_strategy = form.save()
            print('updated_strategy >>> ', updated_strategy)
            # return redirect('/mcdonalds/strategy/update/' + str(new_strategy.strategy_id) + '/')
            return render(request, 'mcdonalds/marketing_strategies_detail.html', {'form': form, 'isAdded':True})
    else:
        try:
            strategy = MarketingStrategies.objects.get(strategy_id=strategy_id)
            form = MarketingStrategyForm(instance=strategy)
            context = {
                'strategy_id': strategy.strategy_id,
                'form': form
            }
        except MarketingStrategies.DoesNotExist:
            # context['form'] = form
            return redirect('/mcdonalds/strategy/add/')
        return render(request, 'mcdonalds/marketing_strategies_detail.html', context)



def delete_strategy(request, strategy_id):
    '''刪除單一行銷策略，最後會回到行銷策略列表'''
    deleted_strategy = MarketingStrategies.objects.get(strategy_id=strategy_id).delete()
    print('deleted_strategy >>> ', deleted_strategy)
    return redirect('/mcdonalds/strategies_list')

def binary_tree(request):
    '''二元樹'''
    # TODO 二元樹
    context = {
        'tab_selected': 'binary_tree'
    }
    return render(request, 'mcdonalds/customer_relationship.html', context)

def survival_rate(request):
    # TODO 存活率 & 留存率
    all_marketing_data = MarketingData.objects.all()
    month_list = [item.date.strftime('%Y-%m-%d') for item in all_marketing_data]
    survival_rate_list = [item.survival_rate for item in all_marketing_data]
    print('month_list >>> ', month_list)
    print('survival_rate_list >>> ', survival_rate_list)

    # Load data
    # df = pd.read_csv(
    #     "https://raw.githubusercontent.com/plotly/datasets/master/finance-charts-apple.csv")
    # df.columns = [col.replace("AAPL.", "") for col in df.columns]

    # Create figure
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(x=month_list, y=survival_rate_list))

    # Set title
    fig.update_layout(
        title_text="存活率"
    )

    # Add range slider
    fig.update_layout(
        xaxis=dict(
            title='時間',
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                         label="1m",
                         step="month",
                         stepmode="backward"),
                    dict(count=3,
                         label="3m",
                         step="month",
                         stepmode="backward"),
                    dict(count=6,
                         label="6m",
                         step="month",
                         stepmode="backward"),
                    dict(count=1,
                         label="1y",
                         step="year",
                         stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(
                visible=True
            ),
            type="date"
        ),
        yaxis=dict(title='存活率 (%)')
    )
    graph = fig.to_html()

    context = {
        'tab_selected': 'survival_rate',
        'survival_rate_graph': graph
    }
    return render(request, 'mcdonalds/customer_relationship.html', context)

def rfm(request):
    # TODO rfm
    context = {
        'tab_selected': 'rfm'
    }
    return render(request, 'mcdonalds/customer_relationship.html', context)

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

