from django.shortcuts import render,redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pandas._libs import json
from datetime import date

from plotly.subplots import make_subplots

from .models import Sales, RFM, Customers, ShoppingRecords, MarketingStrategies, Products, RawMaterial, StrategyProductRel, ProductMaterialRel, StoreDemand, StoreDemandDetails, MarketingData, Stores, Orders, Suppliers
from django.db import connection
from .forms import RawMaterialModelForm, MarketingStrategyForm, OrderForm, StoresContactForm, LoginForm
import plotly.graph_objects as go
from django.core import serializers

from django.contrib.auth import authenticate, login, logout

# Create your views here.
def index(request):
    return render(request, 'mcdonalds/index.html', {})

def stores_contact(request):
    stores = Stores.objects.all()
    context = {
        'store': stores
    }
    return render(request,'mcdonalds/stores_contact.html', context)

def add_stores_contact(request):
    '''新增行銷策略'''
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
    '''查看及修改行銷策略詳細資訊'''
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
    '''刪除單一行銷策略，最後會回到行銷策略列表'''
    deleted_stores_contact = Stores.objects.get(store_id=store_id).delete()
    print('deleted_stores_contact >>> ', deleted_stores_contact)
    return redirect('/mcdonalds/stores_contact')

def suppliers_contact(request):
    suppliers=Suppliers.objects.values()
    return render(request,'mcdonalds/suppliers_contact.html', {'suppliers': suppliers})

#TBD
def add_suppliers_contact(request):
    '''新增供應商通訊錄'''
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
#TBD
def update_suppliers_contact(request, strategy_id):
    '''查看及修改供應商通訊錄'''
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

#TBD
def delete_suppliers_contact(request, strategy_id):
    '''刪除單一供應商通訊錄'''
    deleted_strategy = MarketingStrategies.objects.get(strategy_id=strategy_id).delete()
    print('deleted_strategy >>> ', deleted_strategy)
    return redirect('/mcdonalds/strategies_list')

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
        security_numbers=RawMaterial.objects.values('security_numbers').get(material_id=m_id)['security_numbers']
        if on_hand_inventory<security_numbers:
            create_EOQ_orders(m_id)
        else:
            print('no')

    return render(request,'mcdonalds/store_send_demand.html', {})

def go_to_store_send_demand_page(request):
    return render(request,'mcdonalds/store_send_demand.html', {})

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
    cursor.execute("SELECT store_name, created_date, status, prod_numbers, product_name FROM store_demand INNER JOIN store_demand_details INNER JOIN stores ON store_demand.store_demand_id=store_demand_details.store_demand_id AND store_demand.store_id=stores.store_id INNER JOIN Products on Products.product_id=store_demand_details.product_id")
    store_demand = dictfetchall(cursor)
    for i in store_demand:
        if i['status']==0:
            i['status']='未完成'
            print(i['status'])
        else:
            i['status']='已完成'
    return render(request, 'mcdonalds/store_demand.html', {'store_demand': store_demand})

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
