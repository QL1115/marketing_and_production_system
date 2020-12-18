from django import forms
from .models import RawMaterial


class RawMaterialModelForm(forms.ModelForm):
    class Meta:
        model = RawMaterial
        fields = ('material_name', 'amount','on_hand_inventory','security_numbers')
        widgets = {
            'material_name': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'on_hand_inventory': forms.NumberInput(attrs={'class': 'form-control'}),
            'security_numbers': forms.NumberInput(attrs={'class': 'form-control'})

        }
        labels = {
            'material_name': '原物料名稱',
            'amount': '單位成本',
            'on_hand_inventory': '庫存', 
            'security_numbers':'安全存量'
        }