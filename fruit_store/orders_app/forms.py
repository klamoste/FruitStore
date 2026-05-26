from django import forms
from django.core.validators import RegexValidator
from django.utils import timezone

from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ()


class PaymentForm(forms.Form):
    fulfillment_method = forms.ChoiceField(
        choices=Order.FULFILLMENT_METHOD_CHOICES,
        initial='delivery',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    payment_method = forms.ChoiceField(
        choices=Order.PAYMENT_METHOD_CHOICES,
        initial='COD',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    delivery_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'class': 'form-control',
                'type': 'date',
            }
        )
    )
    delivery_window = forms.ChoiceField(
        choices=Order.DELIVERY_WINDOW_CHOICES,
        required=False,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
    )
    gcash_sender_name = forms.CharField(
        required=False,
        max_length=120,
        validators=[
            RegexValidator(
                regex=r"^[A-Za-z][A-Za-z .'-]*$",
                message="GCash sender name can use letters, spaces, periods, apostrophes, and hyphens.",
            )
        ],
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Name used in the GCash payment',
                'inputmode': 'text',
                'pattern': "[A-Za-z][A-Za-z .'-]*",
            }
        ),
    )
    gcash_reference_number = forms.CharField(
        required=False,
        max_length=60,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-z0-9-]+$',
                message='GCash reference number can use letters, numbers, and hyphens only.',
            )
        ],
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Reference number from your GCash receipt',
                'inputmode': 'text',
                'pattern': '[A-Za-z0-9-]+',
            }
        ),
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
        self.fields['delivery_date'].widget.attrs['min'] = timezone.localdate().isoformat()

    def clean_delivery_date(self):
        delivery_date = self.cleaned_data['delivery_date']
        if delivery_date < timezone.localdate():
            raise forms.ValidationError('Please choose a delivery date that is today or later.')
        return delivery_date

    def clean(self):
        cleaned_data = super().clean()
        fulfillment_method = cleaned_data.get('fulfillment_method')
        payment_method = cleaned_data.get('payment_method')
        delivery_window = cleaned_data.get('delivery_window')
        sender_name = (cleaned_data.get('gcash_sender_name') or '').strip()
        reference_number = (cleaned_data.get('gcash_reference_number') or '').strip()

        if fulfillment_method == 'delivery' and not delivery_window:
            self.add_error('delivery_window', 'Choose a delivery window for this order.')
        if fulfillment_method == 'pickup':
            cleaned_data['delivery_window'] = ''

        if payment_method == 'GCASH':
            if not sender_name:
                self.add_error('gcash_sender_name', 'Enter the sender name used for the GCash payment.')
            if not reference_number:
                self.add_error('gcash_reference_number', 'Enter the GCash reference number.')

        cleaned_data['gcash_sender_name'] = sender_name
        cleaned_data['gcash_reference_number'] = reference_number
        return cleaned_data


class OrderStatusUpdateForm(forms.Form):
    status = forms.ChoiceField(
        choices=Order.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    assigned_courier = forms.CharField(
        required=False,
        max_length=120,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Courier or rider name',
            }
        ),
    )
    internal_note = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Internal handling note for the operations team',
            }
        ),
    )
