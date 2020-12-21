from datetime import date

from django import forms
from model_utils import Choices

from .models import RawMaterial, MarketingStrategies


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
    class Meta:
        model = MarketingStrategies
        fields = ('strategy_name', 'description', 'start_date', 'end_date', 'status')
        STRATEGY_STATUS = Choices(
            (0, 'ENABLED'),
            (1, 'DISABLED')
        )
        widgets = {
            # 'strategy_id': forms.NumberInput(attrs= {'class': 'form-control'}),
            'strategy_name': forms.TextInput(attrs = {'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(format=('%Y-%m-%d'), attrs={'class': 'form-control datepicker'}),
            'end_date': forms.DateInput(format=('%Y-%m-%d'), attrs={'class': 'form-control datepicker'}),
            'status': forms.Select(attrs = {'class': 'form-control'}, choices=STRATEGY_STATUS)

        }
        labels = {
            'strategy_name': '策略名稱',
            'description': '策略內容',
            'start_date': '開始日期',
            'end_date': '結束日期',
            'status': '狀態'
        }

