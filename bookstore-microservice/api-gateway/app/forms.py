from django import forms


class AddToCartForm(forms.Form):
    customer_id = forms.IntegerField(min_value=1, initial=1)
    book_id = forms.IntegerField(min_value=1)
    quantity = forms.IntegerField(min_value=1, initial=1)
    next = forms.CharField(required=False)


class CheckoutForm(forms.Form):
    customer_id = forms.IntegerField(min_value=1, initial=1)
    shipping_address = forms.CharField(max_length=255)
    pay_method = forms.ChoiceField(choices=[('COD', 'COD'), ('CARD', 'CARD'), ('BANKING', 'BANKING')])
    ship_method = forms.ChoiceField(choices=[('STANDARD', 'STANDARD'), ('FAST', 'FAST'), ('EXPRESS', 'EXPRESS')])


class ReviewForm(forms.Form):
    customer_id = forms.IntegerField(min_value=1, initial=1)
    rating = forms.IntegerField(min_value=1, max_value=5)
    comment = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))


class AddBookForm(forms.Form):
    title = forms.CharField(max_length=255)
    author = forms.CharField(max_length=255)
    price = forms.DecimalField(min_value=0)
    stock = forms.IntegerField(min_value=0)
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))
    created_by_staff_id = forms.IntegerField(min_value=1, initial=1)
    image_url = forms.URLField(required=False)


class AddCustomerForm(forms.Form):
    name = forms.CharField(max_length=255)
    email = forms.EmailField()
    address = forms.CharField(max_length=255, required=False)
