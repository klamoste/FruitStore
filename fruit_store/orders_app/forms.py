from django import forms
from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ()


class PaymentForm(forms.Form):
    PAYMENT_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('GCASH', 'GCash'),
    ]
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
