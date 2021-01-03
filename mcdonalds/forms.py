from datetime import date

from django import forms
from model_utils import Choices

from .models import RawMaterial, MarketingStrategies, Orders, Stores, Suppliers


class RawMaterialModelForm(forms.ModelForm):
    class Meta:
        model = RawMaterial
        fields = ('material_id','material_name', 'amount','on_hand_inventory','security_numbers')
        widgets = {
            'material_id': forms.TextInput(attrs={'class': 'form-control'}),
            'material_name': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'on_hand_inventory': forms.NumberInput(attrs={'class': 'form-control'}),
            'security_numbers': forms.NumberInput(attrs={'class': 'form-control'})

        }
        # labels = {
        #     'material_name': '原物料名稱',
        #     'amount': '單位成本',
        #     'on_hand_inventory': '庫存',
        #     'security_numbers':'安全存量'
        # }

class MarketingStrategyForm(forms.ModelForm):

    # product_json = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control mx-sm-3', 'type': 'hidden', 'name': 'product_list'}))

    class Meta:
        model = MarketingStrategies
        fields = ('strategy_name', 'description', 'start_date', 'end_date', 'status')
        STRATEGY_STATUS = Choices(
            (0, 'ENABLED'),
            (1, 'DISABLED')
        )
        widgets = {
            # 'strategy_id': forms.NumberInput(attrs= {'class': 'form-control'}),
            'strategy_name': forms.TextInput(attrs = {'class': 'form-control mx-sm-3', 'name': 'strategy_name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'name': 'description', 'rows': 3}),
            'start_date': forms.DateInput(format=('%Y-%m-%d'), attrs={'class': 'form-control datepicker mx-sm-3', 'name':'start_date'}),
            'end_date': forms.DateInput(format=('%Y-%m-%d'), attrs={'class': 'form-control datepicker mx-sm-3', 'name': 'end_date'}),
            'status': forms.Select(attrs = {'class': 'form-control mx-sm-3', 'name': 'status'}, choices=STRATEGY_STATUS),

        }


class OrderForm(forms.ModelForm):
    
    class Meta:
        model = Orders
        fields = {'order_amount','material','order_date'}
        ORDER_STATUS = Choices(
            (0, '~'),
            (1, '大麥克麵包222'),
            (2, '1/10牛肉餅'),
            (3, '吉士片'),
            (4, '切片生菜'),
            (5, '大麥克醬'),
            (6, '布里歐麵包'),
            (7, '番茄片'),
            (8, '厚切培根'),
            (9, '安格斯牛肉餅'),
            (10, 'BLT燒烤醬'),
            (11, '番茄醬'),
            (12, '薯條'),
            (13, '麥克雞塊'),
            (14, '可樂'),

        )
        widgets = {
            'order_amount': forms.TextInput(attrs={'class': 'form-control'}),
            'material': forms.Select(attrs = {'class': 'form-control'}, choices=ORDER_STATUS),
            #forms.Select(attrs = {'class': 'form-control'}, choices=ORDER_STATUS),
            #choices=RawMaterial.objects.all().values_list('material_id', 'material_name'),
            'order_date': forms.DateInput(format=('%Y-%m-%d'), attrs={'class': 'form-control datepicker'}),
        }
        labels = {
            'order_amount':'訂購數量',
            'material':'訂購商品',
            'order_date':'訂購日期'
        }

class StoresContactForm(forms.ModelForm):
    class Meta:
        model = Stores
        fields = ('store_name', 'store_address', 'store_phone', 'store_region')
        widgets = {
            # 'strategy_id': forms.NumberInput(attrs= {'class': 'form-control'}),
            'store_name': forms.TextInput(attrs = {'class': 'form-control'}),
            'store_address': forms.TextInput(attrs={'class': 'form-control'}),
            'store_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'store_region':  forms.TextInput(attrs={'class': 'form-control'})
        }
        labels = {
            'store_name': '分店名稱',
            'store_address': '地址',
            'store_phone': '連絡電話',
            'store_region': '區域',
        }

class SuppliersContactForm(forms.ModelForm):
    class Meta:
        model = Suppliers
        fields = ('supplier_name', 'supplier_address', 'supplier_phone')
        widgets = {
            # 'strategy_id': forms.NumberInput(attrs= {'class': 'form-control'}),
            'supplier_name': forms.TextInput(attrs = {'class': 'form-control'}),
            'supplier_address': forms.TextInput(attrs={'class': 'form-control'}),
            'supplier_phone': forms.TextInput(attrs={'class': 'form-control'})
        }
        labels = {
            'supplier_name': '供應商名稱',
            'supplier_address': '地址',
            'supplier_phone': '連絡電話',
        }


class LoginForm(forms.Form):
    username = forms.CharField(
        label="帳號",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label="密碼",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

