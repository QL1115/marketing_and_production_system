import math
from django.shortcuts import render,redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pandas._libs import json
from datetime import date, timedelta

from plotly.subplots import make_subplots

from .models import Sales, RFM, Customers, ShoppingRecords, MarketingStrategies, Products, RawMaterial, StrategyProductRel, ProductMaterialRel, StoreDemand, StoreDemandDetails, MarketingData, Stores, Orders, Suppliers
from django.db import connection
from .forms import RawMaterialModelForm, MarketingStrategyForm, OrderForm, StoresContactForm, LoginForm, SuppliersContactForm
import plotly.graph_objects as go
from django.core import serializers
from django.db.models import Sum
from django.contrib.auth import authenticate, login, logout

# Create your views here.
def index(request):
    calculate_EOQ(1)
    for i in range(1,6):
        calculate_ROP(i)
    return render(request, 'mcdonalds/index.html', {})

def stores_contact(request):
    stores = Stores.objects.all()
    context = {
        'store': stores
    }
    return render(request,'mcdonalds/stores_contact.html', context)

def add_stores_contact(request):
    '''新增分店聯絡資訊'''
    if request.method == 'POST':
        form = StoresContactForm(request.POST)
        if form.is_valid():
            new_stores_contact = form.save()
            print('new_stores_contact >>> ', new_stores_contact)
            # return redirect('/mcdonalds/strategy/update/' + str(new_strategy.strategy_id) + '/')
            return render(request, 'mcdonalds/stores_contact_detail.html', {'form': form, 'isAdded':True})
    else:
        form = StoresContactForm()
        return render(request, 'mcdonalds/stores_contact_detail.html', {'form': form})

def update_stores_contact(request, store_id):
    '''查看及修改分店聯絡資訊'''
    if request.method == 'POST':
        form = StoresContactForm(request.POST)
        if form.is_valid():
            store = Stores.objects.get(pk=store_id)
            form = StoresContactForm(request.POST, instance=store)
            updated_stores_contact = form.save()
            print('updated_stores_contact >>> ', updated_stores_contact)
            # return redirect('/mcdonalds/strategy/update/' + str(new_strategy.strategy_id) + '/')
            return render(request, 'mcdonalds/stores_contact_detail.html', {'form': form, 'isAdded':True})
    else:
        try:
            store = Stores.objects.get(store_id=store_id)
            form = StoresContactForm(instance=store)
            context = {
                'store_id': store.store_id,
                'form': form
            }
        except MarketingStrategies.DoesNotExist:
            # context['form'] = form
            return redirect('/mcdonalds/stores_contact/add/')
        return render(request, 'mcdonalds/stores_contact_detail.html', context)

def delete_stores_contact(request, store_id):
    '''刪除單一分店聯絡資訊，最後會回到分店聯絡資訊列表'''
    deleted_stores_contact = Stores.objects.get(store_id=store_id).delete()
    print('deleted_stores_contact >>> ', deleted_stores_contact)
    return redirect('/mcdonalds/stores_contact')

def suppliers_contact(request):
    #suppliers=Suppliers.objects.values()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM raw_material INNER JOIN suppliers ON raw_material.supplier_id = suppliers.supplier_id')
    suppliers = dictfetchall(cursor)
    return render(request,'mcdonalds/suppliers_contact.html', {'suppliers': suppliers})

#TBD
def add_suppliers_contact(request):
    '''新增供應商通訊錄'''
    if request.method == 'POST':
        form = SuppliersContactForm(request.POST)
        if form.is_valid():
            new_contact = form.save()
            print('new_contact >>> ', new_contact)
            # return redirect('/mcdonalds/strategy/update/' + str(new_strategy.strategy_id) + '/')
            return render(request, 'mcdonalds/suppliers_contact_detail.html', {'form': form, 'isAdded':True})
    else:
        form = SuppliersContactForm()
        return render(request, 'mcdonalds/suppliers_contact_detail.html', {'form': form})
#TBD
def update_suppliers_contact(request, supplier_id):
    '''查看及修改供應商通訊錄'''
    if request.method == 'POST':
        form = SuppliersContactForm(request.POST)
        if form.is_valid():
            suppliers_contact = Suppliers.objects.get(pk=supplier_id)
            form = SuppliersContactForm(request.POST, instance=suppliers_contact)
            updated_suppliers_contact = form.save()
            print('updated_strategy >>> ', updated_suppliers_contact)
            # return redirect('/mcdonalds/strategy/update/' + str(new_strategy.strategy_id) + '/')
            return render(request, 'mcdonalds/suppliers_contact_detail.html', {'form': form, 'isAdded':True})
    else:
        try:
            suppliers_contact = Suppliers.objects.get(pk=supplier_id)
            form = SuppliersContactForm(instance=suppliers_contact)
            context = {
                'supplier_id': suppliers_contact.supplier_id,
                'form': form
            }
        except Suppliers.DoesNotExist:
            # context['form'] = form
            return redirect('/mcdonalds/suppliers_contact/add/')
        return render(request, 'mcdonalds/suppliers_contact_detail.html', context)

#TBD
def delete_suppliers_contact(request, supplier_id):
    '''刪除單一供應商通訊錄'''
    deleted_supplier_contact = Suppliers.objects.get(supplier_id=supplier_id).delete()
    print('deleted_supplier_contact>>> ', deleted_supplier_contact)
    return redirect('/mcdonalds/suppliers_contact')

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
    cursor2.execute("SELECT order_id,material_name, order_amount, order_date, status FROM orders INNER JOIN raw_material ON orders.material_id=raw_material.material_id;")
    raw_materials_order = dictfetchall(cursor2)
    print('raw_materials_order >>> ', raw_materials_order)

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
    cursor.execute("SELECT material_id,material_name, amount, on_hand_inventory, security_numbers,supplier_name, quantity,reorder_point FROM raw_material INNER JOIN suppliers ON raw_material.supplier_id=suppliers.supplier_id;")
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

def search_prod_by_category(request, prod_category_num):
    ''' 利用商品類別查詢商品列表 '''
    catgory = ''
    if prod_category_num == 1:
        catgory = '漢堡'
    elif prod_category_num == 2:
        catgory = '點心'
    else:
        catgory = '飲料/湯品'
    product_list = Products.objects.filter(category=catgory)
    # print('product_list >>> ', product_list)
    return JsonResponse({'product_list': serializers.serialize('json', product_list)})

def strategies_list(request):
    '''行銷策略列表'''

    strategies_list = MarketingStrategies.objects.all()
    context = {
        'strategies_list': strategies_list
    }
    return render(request, 'mcdonalds/marketing_strategies_list.html', context)

# def find_strategy_product_rel_by_strid(reqeust, strategy_id):
#     '''由行銷策略 id 尋找對應的「行銷策略與商品」的紀錄'''
#     strtg_prod_rel_list = StrategyProductRel.objects.filter(strategy_id=strategy_id)
#     strtg_prod_rel_list = serializers.serialize('json', strtg_prod_rel_list)
#     print('strtg_prod_rel_list >>> ', strtg_prod_rel_list)
#     return JsonResponse(strtg_prod_rel_list)

@csrf_exempt
def store_strategy(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        print('data', data)
        strategy_name = data['strategy_name']
        start_date = data['start_date']
        end_date = data['end_date']
        status = data['status']
        description = data['description']
        product_list = data['product_list']

        # TODO check POST data
        if not strategy_name or not description:
            return HttpResponse(False)

        strategy = None
        if 'strategy_id' in data:
            strategy_id = data['strategy_id'] # 可能沒有，沒有的話代表是新增行銷策略，若有的話，代表是修改現有的行銷策略
            strategy = MarketingStrategies.objects.get(strategy_id=strategy_id)
        if strategy is None:
            strategy = MarketingStrategies.objects.create(start_date=start_date, end_date=end_date, strategy_name=strategy_name, status=status, description=description)
        try:
            for item in product_list:
                product = Products.objects.get(product_id=item['prod_id'])

                if 'spr_id' in item:
                    str_prod = StrategyProductRel.objects.filter(spr_id=item['spr_id']).first()
                    if str_prod: # 已經有對應的 「商品」- 「行銷策略」了
                        print('有對應的 spr')
                        str_prod.numbers = item['prod_num']
                        str_prod.save()
                    else:
                        print('沒有對應的 spr')
                        StrategyProductRel.objects.create(product=product,
                                                          strategy=strategy,
                                                          numbers=item['prod_num'])
                else: # 沒有對應的 「商品」-「行銷策略」
                    print('沒有 item[\'spr_id\']')
                    StrategyProductRel.objects.create(product=product,
                                                            strategy=strategy,
                                                            numbers=item['prod_num'])
            return HttpResponse(True)
        except Exception as e:
            # return JsonResponse(serializers.serialize('json', {'isStored': 'ERROR'}))
            print('error >>> ', e)
            return HttpResponse(False)
    elif request.method == 'GET':
        strategy_id = request.GET.get('strategy_id')

        if strategy_id:
            try:
                strategy = MarketingStrategies.objects.get(strategy_id=strategy_id)
                strt_prod_list = StrategyProductRel.objects.filter(strategy_id=strategy_id)
                product_list = Products.objects.filter(pk__in=strt_prod_list)
                # product_list = StrategyProductRel.objects.select_related('product_id').all() #.filter(strategy=strategy)
                data = zip(strt_prod_list, product_list)
                return render(request, 'mcdonalds/marketing_strategies_detail.html', {'strategy': strategy, 'data': data})
            except:
                print('error')
                return render(request, 'mcdonalds/marketing_strategies_detail.html', {'strategy': strategy})
        else:
            return render(request, 'mcdonalds/marketing_strategies_detail.html')



def delete_strategy(request, strategy_id):
    '''刪除單一行銷策略，最後會回到行銷策略列表'''
    deleted_strategy = MarketingStrategies.objects.get(strategy_id=strategy_id).delete()
    print('deleted_strategy >>> ', deleted_strategy)
    return redirect('/mcdonalds/strategies_list')

def delete_spr(request, spr_id):
    print('spr_id >>> ', spr_id)
    deleted_spr = StrategyProductRel.objects.get(spr_id=spr_id).delete()
    print('deleted spr >>> ', deleted_spr)
    if deleted_spr:
        return HttpResponse('SUCCESS')
    else:
        return HttpResponse('ERROR')

# def binary_tree(request):
#     '''二元樹'''
#     # TODO 二元樹
#     context = {
#         'tab_selected': 'binary_tree'
#     }
#     return render(request, 'mcdonalds/customer_relationship.html', context)

def survival_rate(request):
    '''存活率 & 留存率'''
    # TODO 留存率
    all_marketing_data = MarketingData.objects.all()
    month_list = [item.date.strftime('%Y-%m-%d') for item in all_marketing_data]
    # 存活率
    survival_rate_list = [item.survival_rate for item in all_marketing_data]
    temp_sr_list = [100] + survival_rate_list # 為了計算留存率，故往後移動一個
    # 留存率
    rr_list = [ round(x/y*100, 2) for x, y in zip(survival_rate_list,temp_sr_list)]
    # print('temp_sr_list', temp_sr_list)
    # print('sr list', survival_rate_list)
    # print('rr list', rr_list)
    # print('size', len(survival_rate_list), len(rr_list))

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Create figure
    # fig = go.Figure()

    fig.add_trace(
        go.Scatter(x=month_list, y=survival_rate_list, name='存活率'), secondary_y=False)

    fig.add_trace(
        go.Scatter(x=month_list, y=rr_list, name="留存率"),
        secondary_y=True,
    )

    # Set title
    fig.update_layout(
        title_text="存活率 & 留存率"
    )

    # Add range slider
    fig.update_layout(
        xaxis=dict(
            title='<b>時間</b>',
            rangeselector=dict(
                buttons=list([
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
        # yaxis=dict(title='存活率 (%)')
    )
    # Set y-axes titles
    fig.update_yaxes(title_text="<b>存活率</b> (%)", secondary_y=False)
    fig.update_yaxes(title_text="<b>留存率</b> (%)", secondary_y=True)
    graph = fig.to_html()

    context = {
        'tab_selected': 'survival_rate',
        'survival_rate_graph': graph
    }
    return render(request, 'mcdonalds/customer_relationship.html', context)

def customer(request, rfm_id):
    '''透過 rfm_id 查詢對應的 customer list'''
    customer_list_serialized = serializers.serialize('json', Customers.objects.filter(rfm__rfm_id=rfm_id))
    # customer_list = Customers.objects.filter(rfm__rfm_id=rfm_id)
    context = {
        'rfm_id': rfm_id,
        'customer_list': customer_list_serialized
    }
    return JsonResponse(context)


def rfm(request):
    rfm_qry_set = RFM.objects.all().order_by('rfm_value')
    # rfm_qry_set = serializers.serialize('json', RFM.objects.all().order_by('rfm_value'),
    #                              fields=('rfm_id', 'actual_resp_rate', 'rfm_value'))

    # # 分頁功能
    # paginator = Paginator(rfm_qry_set, 10)
    # page = request.GET.get('page', 1)
    #
    # if page:
    #     rfm_list = paginator.page(page).object_list
    # else:
    #     rfm_list = paginator.page(1).object_list

    # TODO for dataTable
    # rfm_list = []
    # for rfm in rfm_qry_set:
    #     rfm_list.append({'rfm_id': rfm.rfm_id, 'actual_resp_rate': rfm.actual_resp_rate, 'rfm_value': rfm.rfm_value})
    # # rfm_list = serializers.serialize('json', rfm_list)
    # print('rfm_qry_set >>> ', rfm_list)

    context = {
        'tab_selected': 'rfm',
        # "rfm_list": rfm_list
        "rfm_list": rfm_qry_set
    }
    return render(request, 'mcdonalds/customer_relationship.html', context)

def get_edit_page(request, material_id):
    raw_materials = RawMaterial.objects.get(material_id=material_id)
    print('!')
    print(raw_materials.material_id)

    return render(request,'mcdonalds/update_raw_materials.html', {'raw_materials':raw_materials})


def save_update_raw_materials(request, material_id):
    raw_materials = RawMaterial.objects.get(material_id=material_id)
    form = RawMaterialModelForm(request.POST, instance = raw_materials)

    if form.is_valid():
        form.save()
        return redirect("/mcdonalds/raw_materials")
    return render(request, 'mcdonalds/update_raw_materials.html', {'raw_materials': raw_materials})

@csrf_exempt
def receive_store_demand(request):

    store_id = request.POST.get('store_id', False)
    product_id = request.POST.get('product_id', False)
    product_num = request.POST.get('product_num', False)
    create_store_demand(store_id,product_id,product_num)#建立store_demand＆store_demand_detail
    list_of_number_and_material_id=turn_produtcts_to_raw_materials(product_id)#撈出相關raw_material_id及相對應消耗量
    #print(list)
    for item in range(len(list_of_number_and_material_id)):
        print('id',list_of_number_and_material_id[item][0])
        print('number',list_of_number_and_material_id[item][1])
        m_id=list_of_number_and_material_id[item][0]
        number=list_of_number_and_material_id[item][1]
        #先選取出目前的庫存
        current_on_hand_inventory=RawMaterial.objects.values('on_hand_inventory').get(material_id=m_id)['on_hand_inventory']#type int
        product_num=int(product_num)
        #一建立訂單，庫存就被扣，算出新的庫存
        new_on_hand_inventory=current_on_hand_inventory-product_num*number
        #print('new_on_hand_inventory',new_on_hand_inventory)
        #更新庫存
        RawMaterial.objects.filter(material_id=m_id).update(on_hand_inventory = new_on_hand_inventory)
        #撈出庫存及安全庫存
        RawMaterial.objects.filter(material_id=1).update(security_numbers = 30000000000)
        on_hand_inventory=RawMaterial.objects.values('on_hand_inventory').get(material_id=m_id)['on_hand_inventory']
        reorder_point=RawMaterial.objects.values('reorder_point').get(material_id=m_id)['reorder_point']
        if on_hand_inventory<reorder_point:
            create_EOQ_orders(m_id)
        else:
            print('no')

    stores=Stores.objects.all()
    products=Products.objects.all()
    return render(request,'mcdonalds/store_send_demand.html', {'stores':stores,'products':products})
    #return render(request,'mcdonalds/store_send_demand.html', {})

@csrf_exempt
def go_to_store_send_demand_page(request):
    return render(request,'mcdonalds/store_send_demand.html')

@csrf_exempt
def create_store_demand(store_id,product_id,product_num):
    # call by receive_store_demand
    #建立門市需求單
    product_num=product_num
    today = str(date.today())
    store_demand = StoreDemand.objects.create(store_id=store_id,status=0,created_date=today)
    bigest_id=StoreDemand.objects.latest('store_demand_id').store_demand_id
    #建立門市需求單detail
    store_demand_detail=StoreDemandDetails.objects.create(product_id=product_id,store_demand_id=bigest_id,prod_numbers=product_num)

def turn_produtcts_to_raw_materials(product_id):
    list=ProductMaterialRel.objects.values_list('material_id','numbers').filter(product_id=product_id)#return<QuerySet [(1, 1), (2, 2), (1, 3), (2, 4), (1, 5)]>
    #a[2]=(1, 3) a[2][0]=1 a[2][1]=3
    return list

def create_EOQ_orders(m_id):
    eoq=RawMaterial.objects.values('quantity').get(material_id=m_id)['quantity']
    print('eoq',eoq)
    today = str(date.today())
    Orders.objects.create(order_date=today,status=0,order_amount=eoq,material_id=m_id)
    print('done')


def add_order(request):
    '''新增order'''
    if request.method == 'POST':
        form = OrderForm(request.POST)
        print('here!')
        if form.is_valid():
            new_order = form.save()
            print('new_order >>> ', new_order)
            # return redirect('/mcdonalds/strategy/update/' + str(new_strategy.strategy_id) + '/')
            return render(request, 'mcdonalds/raw_materials_order_create.html', {'form': form, 'isAdded':True})
    else:
        form = OrderForm()
        return render(request, 'mcdonalds/raw_materials_order_create.html', {'form': form})

def store_demand(request):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM store_demand INNER JOIN stores WHERE store_demand.store_id = stores.store_id")
    store_demand = dictfetchall(cursor)
    for i in store_demand:
        if i['status']==0:
            i['status']='未完成'
            print(i['status'])
        else:
            i['status']='已完成'
    return render(request, 'mcdonalds/store_demand.html', {'store_demand': store_demand})

def store_demand_detail(request, store_demand_id):
    #store_demand = StoreDemandDetails.objects.select_related('product').select_related('store_demand').filter(store_demand_id=store_demand_id)
    #store = StoreDemand.objects.filter(store_demand_id = store_demand_id).select_related('stores')
    cursor = connection.cursor()
    cursor.execute('SELECT product_name, prod_numbers FROM store_demand_details INNER JOIN products INNER JOIN store_demand ON store_demand_details.store_demand_id = store_demand.store_demand_id AND store_demand_details.product_id = products.product_id WHERE store_demand_details.store_demand_id = %d'%store_demand_id)
    cursor2 = connection.cursor()
    cursor2.execute('SELECT store_name FROM stores INNER JOIN store_demand ON store_demand.store_id=stores.store_id WHERE store_demand.store_demand_id=%d'%store_demand_id)
    cursor3 = connection.cursor()
    cursor3.execute('SELECT status, created_date FROM store_demand INNER JOIN store_demand_details ON store_demand.store_demand_id=store_demand_details.store_demand_id WHERE store_demand.store_demand_id=%d LIMIT 1' % store_demand_id)

    store_demand = dictfetchall(cursor)
    store = dictfetchall(cursor2)
    demand_detail = dictfetchall(cursor3)
    for i in demand_detail:
        if i['status']==0:
            i['status']='未完成'
            print(i['status'])
        else:
            i['status']='已完成'
    context = {
        'store_demand': store_demand,
        'store': store,
        'demand_detail': demand_detail
    }
    return render(request, 'mcdonalds/store_demand_detail.html', context)

#待完成，是否發送通知?
#有沒有更好的辦法呼叫原頁面?
def raw_material_arrived_store(request, store_demand_id):
    """
    原物料送到分店
    """
    StoreDemand.objects.filter(store_demand_id=store_demand_id).update(status=1)
    cursor = connection.cursor()
    cursor.execute(
        "SELECT store_name, created_date, status FROM store_demand INNER JOIN store_demand_details INNER JOIN stores ON store_demand.store_demand_id=store_demand_details.store_demand_id AND store_demand.store_id=stores.store_id")
    store_demand = dictfetchall(cursor)
    for i in store_demand:
        if i['status'] == 0:
            i['status'] = '未完成'
            print(i['status'])
        else:
            i['status'] = '已完成'
    return render(request, 'mcdonalds/store_demand.html', {'store_demand': store_demand})

#待完成，是否發送通知?
#有沒有更好的辦法呼叫原頁面?
def raw_material_arrived_center(request, order_id):
    Orders.objects.filter(order_id=order_id).update(status=1)
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
@csrf_exempt
def sign_in(request):
    form = LoginForm()
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return render(request, 'mcdonalds/index.html', {})  #重新導向到首頁
    context = {
        'form': form
    }
    return render(request, 'mcdonalds/login.html', context)

# 行銷Dashboard
def marketing_dashboard(request):
    # 前期比較 
    pre_month_list = ['2019-01-31', '2019-02-28', '2019-03-31', '2019-04-30', '2019-05-31', '2019-06-30', '2019-07-31', '2019-08-31', '2019-09-30', '2019-10-31', '2019-11-30', '2019-12-31']
    cur_month_list = ['2020-01-31', '2020-02-29', '2020-03-31', '2020-04-30', '2020-05-31', '2020-06-30', '2020-07-31', '2020-08-31', '2020-09-30', '2020-10-31', '2020-11-30', '2020-12-31']
    monthList = ['Jan.', 'Feb.', 'Mar.', 'Apr.', 'May', 'Jun.', 'Jul.', 'Aug.', 'Sept.', 'Oct.', 'Nov.', 'Dec.']
    pre_sales_data = Sales.objects.filter(date__contains='2019')
    cur_sales_data = Sales.objects.filter(date__contains='2020')
    
    # 2019各月銷售量(Default為漢堡)
    pre_sales_num_list = [pre_sales_data.select_related('product').filter(date__contains=mon, product__category__exact='漢堡').aggregate(Sum('numbers'))['numbers__sum'] for mon in pre_month_list]
    # 2020各月銷售量
    cur_sales_num_list = [cur_sales_data.select_related('product').filter(date__contains=mon, product__category__exact='漢堡').aggregate(Sum('numbers'))['numbers__sum'] for mon in cur_month_list]
    
    # plotly
    # Create figure
    comparison_fig = go.Figure()

    comparison_fig.add_trace(
        go.Scatter(x=monthList, y=pre_sales_num_list, name="2019")) # name -> legend title
    comparison_fig.add_trace(
        go.Scatter(x=monthList, y=cur_sales_num_list, name="2020"))

    # Set title
    comparison_fig.update_layout(
        title_text="前期比較(漢堡)"
    )

    # comparison_fig.update_traces(
        # hoverinfo="name+x+text",
        # line={"width": 0.5},
        # marker={"size": 8},
        # mode="lines+markers",
        # showlegend=False
    # )   
    
    # Add range slider
    comparison_fig.update_layout(
        xaxis=dict(
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
                visible=False
            ),
        ),
        yaxis=dict(title='銷售量')
    )
    comparisonwithprevious_graph = comparison_fig.to_html()
    
    
    # 銷售排行
    product_category_list = ['漢堡', '點心', '飲料/湯品']
    product_sales_2019 = [pre_sales_data.select_related('product').filter(product__category__exact=category).aggregate(Sum('numbers'))['numbers__sum'] for category in product_category_list]
    product_sales_2020 = [cur_sales_data.select_related('product').filter(product__category__exact=category).aggregate(Sum('numbers'))['numbers__sum'] for category in product_category_list]
    
    # plotly
    salesranking_fig = go.Figure()
    salesranking_fig.add_trace(go.Bar(
        y=product_category_list,
        x=product_sales_2019,
        name='2019',
        orientation='h',
        marker=dict(
            color='rgba(246, 78, 139, 0.6)',
            line=dict(color='rgba(246, 78, 139, 1.0)', width=3)
        )
    ))
    salesranking_fig.add_trace(go.Bar(
        y=product_category_list,
        x=product_sales_2020,
        name='2020',
        orientation='h',
        marker=dict(
            color='rgba(58, 71, 80, 0.6)',
            line=dict(color='rgba(58, 71, 80, 1.0)', width=3)
        )
    ))

    salesranking_fig.update_layout(
        barmode='stack',
        title_text='銷售排行'
    ) 
    salesranking_graph = salesranking_fig.to_html()
    
    
    # 各區銷售表現
    store_region_list = ['北區', '中區', '南區', '東區']
    product_sales_2019 = [pre_sales_data.select_related('product').filter(store__store_region=region).aggregate(Sum('numbers'))['numbers__sum']/6 for region in store_region_list]
    product_sales_2020 = [cur_sales_data.select_related('product').filter(store__store_region=region).aggregate(Sum('numbers'))['numbers__sum']/6 for region in store_region_list]
    
    # plotly
    storeperformance_fig = go.Figure()
    storeperformance_fig.add_trace(go.Bar(
        y=store_region_list,
        x=product_sales_2019,
        name='2019',
        orientation='h',
        marker=dict(
            color='rgba(246, 78, 139, 0.6)',
            line=dict(color='rgba(246, 78, 139, 1.0)', width=3)
        )
    ))
    storeperformance_fig.add_trace(go.Bar(
        y=store_region_list,
        x=product_sales_2020,
        name='2020',
        orientation='h',
        marker=dict(
            color='rgba(58, 71, 80, 0.6)',
            line=dict(color='rgba(58, 71, 80, 1.0)', width=3)
        )
    ))

    storeperformance_fig.update_layout(
        barmode='stack',
        title_text='各區銷售表現'
    ) 
    storeperformance_graph = storeperformance_fig.to_html()
    
    
    
    # CVR
    marketing_data = MarketingData.objects.all()
    month_list = [item.date.strftime('%Y-%m-%d') for item in marketing_data]
    cvr_list = [item.cvr for item in marketing_data]
    
    # plotly
    # Create figure
    cvr_fig = go.Figure()

    cvr_fig.add_trace(
        go.Scatter(x=month_list, y=cvr_list))

    # Set title
    cvr_fig.update_layout(
        title_text="CVR"
    )

    # Add range slider
    cvr_fig.update_layout(
        xaxis=dict(
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
                visible=False
            ),
            type="date"
        ),
        yaxis=dict(title='CVR (%)')
    )
    cvr_graph = cvr_fig.to_html()
    returnDict = {'ComparisonWithPrevious_graph': comparisonwithprevious_graph, 'SalesRanking_graph': salesranking_graph, 'StorePerformance_graph': storeperformance_graph, 'cvr_graph': cvr_graph}
    return render(request, 'mcdonalds/marketing_dashboard.html', returnDict)
    
# 行銷Dashboard視窗
def marketing_dashboard_windows(request):
    categoryDict = {'hamburger': '漢堡', 'snack': '點心', 'beverageNsoup': '飲料/湯品'}
    pre_sales_data = Sales.objects.filter(date__contains='2019')
    cur_sales_data = Sales.objects.filter(date__contains='2020')
    
    graph =  request.GET['graph']
    
    # 前期比較
    if graph == 'ComparisonWithPrevious':
        hamburgerDict = {'1': '大麥克', '2': '雙層牛肉吉事堡', '3': '嫩煎雞腿堡', '4': '麥香雞', '5': '勁辣雞腿堡', '6': '黃金起司豬排堡', '7': '麥香魚', '8': '煙燻雞肉長堡', '9': '薑燒豬肉長堡', '10': 'BLT 安格斯黑牛堡',
                    '11': 'BLT 辣脆雞腿堡', '12': 'BLT 嫩煎雞腿堡', '13': '蕈菇安格斯黑牛堡', '14': '金銀招財薯來堡 (牛)', '15': '金銀招財薯來堡 (雞)', '16': '金銀招財福堡', '17': '法式芥末香雞堡', '18': '漢堡', '19': '吉事漢堡'}
        snackDict = {'1': '麥克雞塊', '2': '麥脆雞腿', '3': '麥脆雞翅', '4': '凱薩脆雞沙拉', '5': '義式烤雞沙拉', '6': '快樂兒童餐', '7': '搖搖樂雞腿排', '8': '勁辣香雞翅', '9': '酥嫩雞翅', '10': '蘋果派',
                     '11': '水果袋', '12': '薯餅', '13': '海苔搖搖粉', '14': '蔥辣搖搖粉', '15': '薯條', '16': '四季沙拉', '17': 'OREO冰炫風', '18': '蛋捲冰淇淋', '19': '大蛋捲冰淇淋'}
        beverageNsoupDict = {'1': '玉米湯', '2': '熱紅茶', '3': '熱奶茶', '4': '鮮乳', '5': '可口可樂', '6': '可口可樂 zero', '7': '雪碧', '8': '冰紅茶 (檸檬風味)', '9': '冰紅茶 (無糖)', '10': '冰綠茶 (無糖)', '11': '冰奶茶', '12': '柳橙汁'}
        
        category = request.GET['category']
        selectedItem = request.GET['selectedItem']
        
        if category == 'hamburger':
            selected = hamburgerDict.get(selectedItem)
        elif category == 'snack':
            selected = snackDict.get(selectedItem)
        elif category == 'beverageNsoup':
            selected = beverageNsoupDict.get(selectedItem)
        
        # 前期比較 
        pre_month_list = ['2019-01-31', '2019-02-28', '2019-03-31', '2019-04-30', '2019-05-31', '2019-06-30', '2019-07-31', '2019-08-31', '2019-09-30', '2019-10-31', '2019-11-30', '2019-12-31']
        cur_month_list = ['2020-01-31', '2020-02-29', '2020-03-31', '2020-04-30', '2020-05-31', '2020-06-30', '2020-07-31', '2020-08-31', '2020-09-30', '2020-10-31', '2020-11-30', '2020-12-31']
        month_list = pre_month_list + cur_month_list
        
        # 2019各月銷售量
        pre_sales_num_list = [pre_sales_data.select_related('product').filter(date__contains=mon, product__product_name__contains=selected).aggregate(Sum('numbers'))['numbers__sum'] for mon in pre_month_list]
        # 2020各月銷售量
        cur_sales_num_list = [cur_sales_data.select_related('product').filter(date__contains=mon, product__product_name__contains=selected).aggregate(Sum('numbers'))['numbers__sum'] for mon in cur_month_list]
        
        # plotly
        # Create figure
        comparison_window_fig = go.Figure()

        comparison_window_fig.add_trace(
            go.Scatter(x=month_list, y=pre_sales_num_list, name="2019")) # name -> legend title
        comparison_window_fig.add_trace(
            go.Scatter(x=month_list, y=cur_sales_num_list, name="2020"))

        # Set title
        comparison_window_fig.update_layout(
            title_text=selected
        )

        # comparison_fig.update_traces(
            # hoverinfo="name+x+text",
            # line={"width": 0.5},
            # marker={"size": 8},
            # mode="lines+markers",
            # showlegend=False
        # )   
        
        # Add range slider
        comparison_window_fig.update_layout(
            xaxis=dict(
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
            ),
            yaxis=dict(title='銷售量')
        )
        
        window_graph = comparison_window_fig.to_html()
    # 銷售排行
    elif graph == 'SalesRanking':
        category = request.GET['category']
        
        product_sales_2019 = [pre_sales_data.select_related('product').filter(product__category__exact=categoryDict.get(category)).values('product__product_name').annotate(total=Sum('numbers'))][0]
        total_2019 = [x.get('total') for x in product_sales_2019]
        product_2019 = [x.get('product__product_name') for x in product_sales_2019]

        product_sales_2020 = [cur_sales_data.select_related('product').filter(product__category__exact=categoryDict.get(category)).values('product__product_name').annotate(total=Sum('numbers'))][0]
        total_2020 = [x.get('total') for x in product_sales_2020]
        product_2020 = [x.get('product__product_name') for x in product_sales_2020]
        
        # plotly
        salesranking_window_fig = go.Figure()
        salesranking_window_fig.add_trace(go.Bar(
            y=product_2019,
            x=total_2019,
            name='2019',
            orientation='h',
            marker=dict(
                color='rgba(246, 78, 139, 0.6)',
                line=dict(color='rgba(246, 78, 139, 1.0)', width=3)
            )
        ))
        salesranking_window_fig.add_trace(go.Bar(
            y=product_2020,
            x=total_2020,
            name='2020',
            orientation='h',
            marker=dict(
                color='rgba(58, 71, 80, 0.6)',
                line=dict(color='rgba(58, 71, 80, 1.0)', width=3)
            )
        ))

        salesranking_window_fig.update_layout(
            barmode='stack',
            title_text='銷售排行',
            autosize=False,
            width=800,
            height=550,
            yaxis={'categoryorder':'total ascending'}  

        ) 
        window_graph = salesranking_window_fig.to_html()
    # 各店銷售表現
    elif graph == 'StorePerformance':
        regionDict = {'north': '北區', 'central': '中區', 'south': '南區', 'east': '東區'}
        region = request.GET['region']
        
        product_sales_2019 = [pre_sales_data.select_related('store').filter(store__store_region=regionDict.get(region)).values('store__store_name').annotate(total=Sum('numbers'))][0]
        total_2019 = [x.get('total') for x in product_sales_2019]
        store_2019 = [x.get('store__store_name') for x in product_sales_2019]
        
        product_sales_2020 = [pre_sales_data.select_related('store').filter(store__store_region=regionDict.get(region)).values('store__store_name').annotate(total=Sum('numbers'))][0]
        total_2020 = [x.get('total') for x in product_sales_2020]
        store_2020 = [x.get('store__store_name') for x in product_sales_2020]
        
        # plotly
        storeperformance_window_fig = go.Figure()
        storeperformance_window_fig.add_trace(go.Bar(
            y=store_2019,
            x=total_2019,
            name='2019',
            orientation='h',
            marker=dict(
                color='rgba(246, 78, 139, 0.6)',
                line=dict(color='rgba(246, 78, 139, 1.0)', width=3)
            )
        ))
        storeperformance_window_fig.add_trace(go.Bar(
            y=store_2020,
            x=total_2020,
            name='2020',
            orientation='h',
            marker=dict(
                color='rgba(58, 71, 80, 0.6)',
                line=dict(color='rgba(58, 71, 80, 1.0)', width=3)
            )
        ))

        storeperformance_window_fig.update_layout(
            barmode='stack',
            title_text='各店銷售表現'
        ) 
        window_graph = storeperformance_window_fig.to_html()
        
    # CVR
    elif graph == 'CVR':
        marketing_data = MarketingData.objects.all()
        month_list = [item.date.strftime('%Y-%m-%d') for item in marketing_data]
        cvr_list = [item.cvr for item in marketing_data]
        
        # plotly
        # Create figure
        cvr_fig = go.Figure()

        cvr_fig.add_trace(
            go.Scatter(x=month_list, y=cvr_list))

        # Set title
        cvr_fig.update_layout(
            title_text="CVR"
        )

        # Add range slider
        cvr_fig.update_layout(
            xaxis=dict(
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
            yaxis=dict(title='CVR (%)')
        )
        window_graph = cvr_fig.to_html()
    return JsonResponse({'WindowGraph': window_graph})

def calculate_EOQ(product_id):
    #經濟訂貨量=（2×年需求量×訂貨成本/(單價×儲存成本百分數)）^0.5
    #假設儲存成本百分數=30%，訂貨成本為購買成本為(單價*2000)元
    year = timedelta(days=365)
    four_years_ago = str(date.today()- 3 * year)
    two_years_ago = str(date.today())

    cursor = connection.cursor()
    cursor.execute('SELECT SUM(prod_numbers) FROM store_demand_details INNER JOIN store_demand ON store_demand_details.store_demand_id = store_demand.store_demand_id WHERE created_date BETWEEN "%s" AND "%s" AND product_id = %s'%(four_years_ago, two_years_ago, product_id))
    year_product_demand = dictfetchall(cursor)
    list_of_number_and_material_id = turn_produtcts_to_raw_materials(product_id)

    for item in range(len(list_of_number_and_material_id)):
        print('material_id',list_of_number_and_material_id[item][0])
        print('quantity',list_of_number_and_material_id[item][1])
        material_id=list_of_number_and_material_id[item][0]
        quantity=list_of_number_and_material_id[item][1]

        amount = RawMaterial.objects.values_list('amount').get(material_id=material_id)# 一個原料多少錢
        year_material_demand = quantity * year_product_demand[0]['SUM(prod_numbers)']
        EOQ = math.pow(((2 * year_material_demand/3) * (amount[0]*2000)) / (amount[0] * 0.3), 0.5)
        RawMaterial.objects.filter(material_id=material_id).update(quantity=EOQ)
        print("material id:",material_id, "EOQ:", EOQ)

    return EOQ

def calculate_ROP(material_id):
    #再訂貨點=平均日需求×訂貨天數+安全儲備量
    consumption_rate = RawMaterial.objects.values_list('consumption_rate').get(material_id=material_id)
    lead_time = RawMaterial.objects.values_list('lead_time').get(material_id=material_id)
    security_numbers = RawMaterial.objects.values_list('security_numbers').get(material_id=material_id)

    ROP = consumption_rate[0] * lead_time[0] + security_numbers[0]
    RawMaterial.objects.filter(material_id=material_id).update(reorder_point=ROP)
    print("ROP:", ROP)
    return ROP
