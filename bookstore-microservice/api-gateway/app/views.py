from decimal import Decimal
from functools import wraps

import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from .forms import AddToCartForm, CheckoutForm, LoginForm, RegisterCustomerForm, ReviewForm, StaffBookForm
from .models import UserProfile

DEFAULT_TIMEOUT = 8
PLACEHOLDER_IMAGE = 'https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=900&q=60'

SERVICES = {
    'book': 'http://book-service:8000',
    'cart': 'http://cart-service:8000',
    'order': 'http://order-service:8000',
    'review': 'http://comment-rate-service:8000',
    'recommend': 'http://recommender-ai-service:8000',
    'customer': 'http://customer-service:8000',
}


def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            profile = getattr(request.user, 'profile', None)
            if not profile or profile.role != role:
                messages.error(request, 'Bạn không có quyền truy cập chức năng này.')
                return redirect('home')
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def _request(method, url, **kwargs):
    kwargs.setdefault('timeout', DEFAULT_TIMEOUT)
    try:
        response = requests.request(method, url, **kwargs)
        data = None
        if response.text:
            try:
                data = response.json()
            except ValueError:
                data = response.text
        return response.status_code, data, None
    except requests.RequestException as exc:
        return None, None, str(exc)


def _book_image(book):
    return book.get('image_url') or PLACEHOLDER_IMAGE


def _profile(request):
    return getattr(request.user, 'profile', None) if request.user.is_authenticated else None


def _customer_id(request):
    profile = _profile(request)
    return profile.customer_id if profile and profile.role == 'customer' else None


def _context(request):
    profile = _profile(request)
    cart_count = 0
    if profile and profile.role == 'customer' and profile.customer_id:
        cart, _ = _get_cart(profile.customer_id)
        if cart:
            cart_count = sum(int(i.get('quantity', 0)) for i in cart.get('items', []))
    return {
        'demo_customer_id': profile.customer_id if profile and profile.customer_id else None,
        'cart_count': cart_count,
        'current_role': profile.role if profile else None,
    }


def _get_books(params=None):
    status, data, error = _request('GET', f"{SERVICES['book']}/books/", params=params)
    if error or status != 200 or not isinstance(data, list):
        return [], error or f'book-service error: {status}'
    for b in data:
        b['display_image'] = _book_image(b)
    return data, None


def _get_book(book_id):
    status, data, error = _request('GET', f"{SERVICES['book']}/books/{book_id}/")
    if error or status != 200 or not isinstance(data, dict):
        return None, error or f'book not found: {status}'
    data['display_image'] = _book_image(data)
    return data, None


def _get_cart(customer_id):
    status, data, error = _request('GET', f"{SERVICES['cart']}/carts/{customer_id}/")
    if error or status != 200 or not isinstance(data, dict):
        return None, error or f'cart-service error: {status}'
    return data, None


def _enrich_cart(cart):
    enriched = []
    total_amount = Decimal('0')
    total_items = 0
    for item in cart.get('items', []):
        book, _ = _get_book(item['book_id'])
        price = Decimal(str(book.get('price', '0'))) if book else Decimal('0')
        quantity = int(item.get('quantity', 0))
        subtotal = price * quantity
        total_amount += subtotal
        total_items += quantity
        enriched.append(
            {
                'id': item['id'],
                'book_id': item['book_id'],
                'quantity': quantity,
                'price': price,
                'subtotal': subtotal,
                'book': book,
                'image': _book_image(book or {}),
            }
        )
    return enriched, total_items, total_amount


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = RegisterCustomerForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        if User.objects.filter(username=email).exists():
            messages.error(request, 'Email đã tồn tại trong hệ thống local.')
            return render(request, 'register.html', {'form': form, **_context(request)})

        payload = {
            'name': form.cleaned_data['name'],
            'email': email,
            'address': form.cleaned_data['address'],
        }
        status, data, error = _request('POST', f"{SERVICES['customer']}/customers/", json=payload)
        if error or status not in (200, 201):
            messages.error(request, f'Không thể tạo customer: {error or data}')
            return render(request, 'register.html', {'form': form, **_context(request)})

        customer_data = data.get('customer') if isinstance(data, dict) and 'customer' in data else data
        customer_id = customer_data.get('id') if isinstance(customer_data, dict) else None
        if not customer_id:
            messages.error(request, 'Customer tạo thành công nhưng thiếu customer_id.')
            return render(request, 'register.html', {'form': form, **_context(request)})

        user = User.objects.create_user(
            username=email,
            email=email,
            password=form.cleaned_data['password'],
            first_name=form.cleaned_data['name'],
        )
        UserProfile.objects.create(user=user, role='customer', customer_id=customer_id)
        login(request, user)
        messages.success(request, 'Đăng ký thành công, đã đăng nhập.')
        return redirect('books')

    return render(request, 'register.html', {'form': form, **_context(request)})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['email'],
            password=form.cleaned_data['password'],
        )
        if not user:
            messages.error(request, 'Sai thông tin đăng nhập.')
        else:
            login(request, user)
            profile = getattr(user, 'profile', None)
            if profile and profile.role == 'staff':
                return redirect('staff-dashboard')
            return redirect('home')
    return render(request, 'login.html', {'form': form, **_context(request)})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Đăng xuất thành công.')
    return redirect('login')


def home_view(request):
    books, book_error = _get_books()
    _, review_data, review_error = _request('GET', f"{SERVICES['review']}/reviews/")

    cart_items = 0
    cart_error = None
    cid = _customer_id(request)
    if cid:
        cart, cart_error = _get_cart(cid)
        cart_items = sum(int(i.get('quantity', 0)) for i in (cart or {}).get('items', [])) if cart else 0

    metrics = {
        'book_count': len(books),
        'review_count': len(review_data) if isinstance(review_data, list) else 0,
        'cart_items': cart_items,
    }
    return render(request, 'home.html', {'metrics': metrics, 'book_error': book_error, 'review_error': review_error, 'cart_error': cart_error, **_context(request)})


@login_required
@role_required('customer')
def books_view(request):
    search = request.GET.get('q', '').strip().lower()
    sort = request.GET.get('sort', 'name_asc')

    books, error = _get_books()
    if search:
        books = [b for b in books if search in b.get('title', '').lower() or search in b.get('author', '').lower()]
    if sort == 'price_asc':
        books = sorted(books, key=lambda x: Decimal(str(x.get('price', 0))))
    elif sort == 'price_desc':
        books = sorted(books, key=lambda x: Decimal(str(x.get('price', 0))), reverse=True)
    else:
        books = sorted(books, key=lambda x: x.get('title', '').lower())

    return render(request, 'books.html', {'books': books, 'error': error, 'q': request.GET.get('q', ''), 'sort': sort, **_context(request)})


@login_required
@role_required('customer')
def book_detail_view(request, book_id):
    book, error = _get_book(book_id)
    _, review_data, review_error = _request('GET', f"{SERVICES['review']}/reviews/book/{book_id}/")
    reviews = review_data[:5] if isinstance(review_data, list) else []
    _, rec_data, rec_error = _request('GET', f"{SERVICES['recommend']}/recommendations/")
    recommendations = rec_data.get('recommendations', [])[:4] if isinstance(rec_data, dict) else []
    return render(request, 'book_detail.html', {'book': book, 'error': error, 'reviews': reviews, 'review_error': review_error, 'recommendations': recommendations, 'rec_error': rec_error, **_context(request)})


@login_required
@role_required('customer')
def cart_add_view(request):
    if request.method != 'POST':
        return redirect('books')

    form = AddToCartForm(request.POST)
    next_url = request.POST.get('next') or 'books'
    if not form.is_valid():
        messages.error(request, 'Dữ liệu thêm giỏ hàng không hợp lệ.')
        return redirect(next_url)

    cid = _customer_id(request)
    status, data, error = _request('POST', f"{SERVICES['cart']}/cart-items/", json={'customer_id': cid, 'book_id': form.cleaned_data['book_id'], 'quantity': form.cleaned_data['quantity']})
    if error or status not in (200, 201):
        messages.error(request, f'Add to cart failed: {error or data}')
    else:
        messages.success(request, 'Đã thêm sách vào giỏ hàng.')
    return redirect(next_url)


@login_required
@role_required('customer')
def cart_view(request):
    cid = _customer_id(request)
    cart, error = _get_cart(cid)
    enriched_items, total_items, total_amount = ([], 0, Decimal('0'))
    if cart:
        enriched_items, total_items, total_amount = _enrich_cart(cart)
    return render(request, 'cart.html', {'items': enriched_items, 'total_items': total_items, 'total_amount': total_amount, 'error': error, **_context(request)})


@login_required
@role_required('customer')
def cart_item_update_view(request, item_id):
    if request.method != 'POST':
        return redirect('cart')

    current_quantity = int(request.POST.get('current_quantity', 1))
    action = request.POST.get('action')
    quantity = int(request.POST.get('quantity', current_quantity))
    if action == 'increase':
        quantity = current_quantity + 1
    elif action == 'decrease':
        quantity = max(1, current_quantity - 1)

    status, data, error = _request('PUT', f"{SERVICES['cart']}/cart-items/{item_id}/", json={'quantity': quantity})
    if error or status not in (200, 202):
        messages.error(request, f'Update cart failed: {error or data}')
    else:
        messages.success(request, 'Cập nhật số lượng thành công.')
    return redirect('cart')


@login_required
@role_required('customer')
def cart_item_delete_view(request, item_id):
    if request.method != 'POST':
        return redirect('cart')
    status, data, error = _request('DELETE', f"{SERVICES['cart']}/cart-items/{item_id}/")
    if error or status not in (200, 202, 204):
        messages.error(request, f'Remove item failed: {error or data}')
    else:
        messages.success(request, 'Đã xóa item khỏi giỏ hàng.')
    return redirect('cart')


@login_required
@role_required('customer')
def checkout_view(request):
    cid = _customer_id(request)
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            payload = {
                'customer_id': cid,
                'shipping_address': form.cleaned_data['shipping_address'],
                'pay_method': form.cleaned_data['pay_method'],
                'ship_method': form.cleaned_data['ship_method'],
            }
            status, data, error = _request('POST', f"{SERVICES['order']}/orders/", json=payload)
            request.session['order_result'] = data or {'error': error}
            request.session['order_status_code'] = status or 503
            if error or status not in (200, 201):
                messages.error(request, f'Tạo order thất bại: {error or data}')
            else:
                messages.success(request, 'Tạo order thành công.')
            return redirect('order-result')
    else:
        profile = _profile(request)
        form = CheckoutForm(initial={'shipping_address': request.user.first_name and '', 'pay_method': 'COD', 'ship_method': 'STANDARD'})

    cart, cart_error = _get_cart(cid)
    items, total_items, total_amount = ([], 0, Decimal('0'))
    if cart:
        items, total_items, total_amount = _enrich_cart(cart)

    return render(request, 'checkout.html', {'form': form, 'items': items, 'total_items': total_items, 'total_amount': total_amount, 'cart_error': cart_error, **_context(request)})


@login_required
@role_required('customer')
def my_orders_view(request):
    cid = _customer_id(request)
    status, data, error = _request('GET', f"{SERVICES['order']}/orders/")
    orders = []
    if isinstance(data, list):
        orders = [o for o in data if o.get('customer_id') == cid]
    return render(request, 'my_orders.html', {'orders': orders, 'error': error if error else (None if status == 200 else f'order-service error: {status}'), **_context(request)})


@login_required
@role_required('customer')
def order_result_view(request):
    result = request.session.get('order_result') or {}
    status_code = request.session.get('order_status_code', 200)
    success = isinstance(status_code, int) and 200 <= status_code < 300
    return render(request, 'order_result.html', {'result': result, 'status_code': status_code, 'success': success, 'items': result.get('items', []) if isinstance(result, dict) else [], **_context(request)})


@login_required
@role_required('customer')
def reviews_view(request, book_id):
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            payload = {'customer_id': _customer_id(request), 'book_id': book_id, 'rating': form.cleaned_data['rating'], 'comment': form.cleaned_data['comment']}
            status, data, error = _request('POST', f"{SERVICES['review']}/reviews/", json=payload)
            if error or status not in (200, 201):
                messages.error(request, f'Gửi review thất bại: {error or data}')
            else:
                messages.success(request, 'Gửi review thành công.')
            return redirect('reviews', book_id=book_id)
    else:
        form = ReviewForm()

    book, book_error = _get_book(book_id)
    _, reviews, review_error = _request('GET', f"{SERVICES['review']}/reviews/book/{book_id}/")
    reviews = reviews if isinstance(reviews, list) else []
    avg_rating = round(sum(r.get('rating', 0) for r in reviews) / len(reviews), 2) if reviews else 0
    return render(request, 'reviews.html', {'book': book, 'book_error': book_error, 'reviews': reviews, 'review_error': review_error, 'avg_rating': avg_rating, 'form': form, **_context(request)})


@login_required
@role_required('customer')
def recommendations_view(request):
    _, payload, error = _request('GET', f"{SERVICES['recommend']}/recommendations/")
    recs = payload.get('recommendations', []) if isinstance(payload, dict) else []
    for r in recs:
        if isinstance(r.get('book'), dict):
            r['book']['display_image'] = _book_image(r['book'])
            r['reason'] = f"Avg rating {r.get('avg_rating', 0)} từ {r.get('review_count', 0)} review"
    return render(request, 'recommendations.html', {'recommendations': recs, 'error': error, **_context(request)})


@login_required
@role_required('staff')
def staff_dashboard_view(request):
    books, error = _get_books()
    form = StaffBookForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        profile = _profile(request)
        payload = {
            'title': form.cleaned_data['title'],
            'author': form.cleaned_data['author'],
            'price': str(form.cleaned_data['price']),
            'stock': form.cleaned_data['stock'],
            'description': form.cleaned_data['description'],
            'image_url': form.cleaned_data['image_url'],
            'created_by_staff_id': profile.staff_id,
        }
        status, data, req_error = _request('POST', f"{SERVICES['book']}/books/", json=payload)
        if req_error or status not in (200, 201):
            messages.error(request, f'Tạo sách thất bại: {req_error or data}')
        else:
            messages.success(request, 'Tạo sách thành công.')
        return redirect('staff-dashboard')

    return render(request, 'staff_dashboard.html', {'books': books, 'error': error, 'form': form, **_context(request)})


@login_required
@role_required('staff')
def staff_book_edit_view(request, book_id):
    book, error = _get_book(book_id)
    if not book:
        messages.error(request, error or 'Không tìm thấy sách.')
        return redirect('staff-dashboard')

    form = StaffBookForm(request.POST or None, initial=book)
    if request.method == 'POST' and form.is_valid():
        profile = _profile(request)
        payload = {
            'title': form.cleaned_data['title'],
            'author': form.cleaned_data['author'],
            'price': str(form.cleaned_data['price']),
            'stock': form.cleaned_data['stock'],
            'description': form.cleaned_data['description'],
            'image_url': form.cleaned_data['image_url'],
            'created_by_staff_id': profile.staff_id,
        }
        status, data, req_error = _request('PUT', f"{SERVICES['book']}/books/{book_id}/", json=payload)
        if req_error or status not in (200, 202):
            messages.error(request, f'Cập nhật sách thất bại: {req_error or data}')
        else:
            messages.success(request, 'Cập nhật sách thành công.')
            return redirect('staff-dashboard')

    return render(request, 'staff_book_edit.html', {'form': form, 'book': book, **_context(request)})


@login_required
@role_required('staff')
def staff_book_delete_view(request, book_id):
    if request.method == 'POST':
        status, data, error = _request('DELETE', f"{SERVICES['book']}/books/{book_id}/")
        if error or status not in (200, 202, 204):
            messages.error(request, f'Xóa sách thất bại: {error or data}')
        else:
            messages.success(request, 'Đã xóa sách.')
    return redirect('staff-dashboard')
