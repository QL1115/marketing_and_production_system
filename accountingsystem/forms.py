from .models import Cashinbanks, Depositaccount
from django import forms

class CashinbanksForm(forms.ModelForm):

    class Meta:
        model = Cashinbanks
        fields = ('bank_name', 'bank_account_number', 'currency', 'foreign_currency_amount', 'ntd_amount')

class DepositAccountForm(forms.ModelForm):
    class Meta:
        model = Depositaccount
        # fields = '__all__'
        fields = ('bank_name', 'bank_account_number', 'currency', 'foreign_currency_amount',
                  'ntd_amount', 'plege', 'start_date', 'end_date')