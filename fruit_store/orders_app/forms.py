from django import forms
from datetime import time
from django.utils import timezone
from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ()


class PaymentMethodRadioSelect(forms.RadioSelect):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        return super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)


class PaymentForm(forms.Form):
    DELIVERY_TIME_CHOICES = [
        (Order.DELIVERY_PERIOD_MORNING, 'Morning'),
        (Order.DELIVERY_PERIOD_AFTERNOON, 'Afternoon'),
    ]
    
    payment_method = forms.ChoiceField(
        choices=Order.PAYMENT_METHOD_CHOICES,
        initial=Order.PAYMENT_METHOD_COD,
        widget=PaymentMethodRadioSelect(attrs={'class': 'form-check-input'})
    )
    gcash_sender_name = forms.CharField(
        required=False,
        max_length=120,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter the GCash account name used for payment.',
            }
        ),
        label='GCash Sender Name',
    )
    gcash_reference = forms.CharField(
        required=False,
        max_length=80,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter your GCash reference number.',
            }
        ),
        label='GCash Reference Number',
    )
    requested_delivery_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'class': 'form-control',
                'type': 'date',
            }
        ),
        label='Delivery Date',
    )
    requested_delivery_time = forms.ChoiceField(
        choices=DELIVERY_TIME_CHOICES,
        initial=Order.DELIVERY_PERIOD_MORNING,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Delivery Window',
    )
    customer_note = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Add delivery notes, preferred handling instructions, or any message for your order.',
            }
        ),
        label='Order Note',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['requested_delivery_date'].widget.attrs['min'] = timezone.localdate().isoformat()

    def clean_requested_delivery_date(self):
        delivery_date = self.cleaned_data['requested_delivery_date']
        if delivery_date < timezone.localdate():
            raise forms.ValidationError('Please choose a delivery date that is today or later.')
        return delivery_date

    def clean_requested_delivery_time(self):
        delivery_window = self.cleaned_data['requested_delivery_time']
        if delivery_window == Order.DELIVERY_PERIOD_MORNING:
            return time(9, 0)
        if delivery_window == Order.DELIVERY_PERIOD_AFTERNOON:
            return time(15, 0)
        raise forms.ValidationError('Please choose a valid delivery window.')

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        sender_name = (cleaned_data.get('gcash_sender_name') or '').strip()
        reference = (cleaned_data.get('gcash_reference') or '').strip().upper()

        if payment_method == Order.PAYMENT_METHOD_GCASH:
            if not sender_name:
                self.add_error('gcash_sender_name', 'Enter the GCash sender name used for this payment.')
            if not reference:
                self.add_error('gcash_reference', 'Enter the GCash reference number before placing the order.')
        else:
            sender_name = ''
            reference = ''

        cleaned_data['gcash_sender_name'] = sender_name
        cleaned_data['gcash_reference'] = reference
        return cleaned_data
