from django import forms


class CartAddProductForm(forms.Form):
    quantity = forms.IntegerField()

    update = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.HiddenInput
    )
