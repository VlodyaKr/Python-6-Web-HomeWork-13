from django.forms import ModelForm
from .models import Balance, Category


class CategoryForm(ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        exclude = ['dr_cr']


class BalanceForm(ModelForm):
    class Meta:
        model = Balance
        fields = ['sum']
        exclude = ['category']
