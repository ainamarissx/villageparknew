from django import forms

class ReceiptUploadForm(forms.Form):
    payment_method = forms.ChoiceField(
        choices=[('Account Transfer', 'Account Transfer'), ('QR Code', 'QR Code')],
        widget=forms.RadioSelect,
        label="Payment Method"
    )
    receipt = forms.ImageField(label='Upload Payment Receipt', required=True)
