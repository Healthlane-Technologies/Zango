from django import forms

from .models import OrderModel



class OrderForm(forms.ModelForm):
    class Meta:
        model = OrderModel
        fields = ['order_dispense_date', 'patient_benefit', 'order_note']