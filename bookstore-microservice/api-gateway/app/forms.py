from django import forms


class RegisterCustomerForm(forms.Form):
    name = forms.CharField(max_length=255)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    address = forms.CharField(max_length=255, required=False)


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class AddToCartForm(forms.Form):
    book_id = forms.IntegerField(min_value=1)
    quantity = forms.IntegerField(min_value=1, initial=1)
    next = forms.CharField(required=False)


class CheckoutForm(forms.Form):
    shipping_address = forms.CharField(max_length=255)
    pay_method = forms.ChoiceField(choices=[('COD', 'COD'), ('CARD', 'CARD'), ('BANKING', 'BANKING')])
    ship_method = forms.ChoiceField(choices=[('STANDARD', 'STANDARD'), ('FAST', 'FAST'), ('EXPRESS', 'EXPRESS')])


class ReviewForm(forms.Form):
    rating = forms.IntegerField(min_value=1, max_value=5)
    comment = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))


class StaffBookForm(forms.Form):
    title = forms.CharField(max_length=255)
    author = forms.CharField(max_length=255)
    price = forms.DecimalField(min_value=0)
    stock = forms.IntegerField(min_value=0)
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))
    image_url = forms.URLField(required=False)
