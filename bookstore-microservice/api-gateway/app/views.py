from decimal import Decimal

import requests
from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import AddBookForm, AddCustomerForm, AddToCartForm, CheckoutForm, ReviewForm

DEFAULT_CUSTOMER_ID = 1
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


def _cart_count(customer_id=DEFAULT_CUSTOMER_ID):
    cart, _ = _get_cart(customer_id)
    if not cart:
        return 0
    return sum(int(i.get('quantity', 0)) for i in cart.get('items', []))


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


def _common_context(customer_id=DEFAULT_CUSTOMER_ID):
    return {'demo_customer_id': customer_id, 'cart_count': _cart_count(customer_id)}


def home_view(request):
    books, book_error = _get_books()
    _, review_data, review_error = _request('GET', f"{SERVICES['review']}/reviews/")
    cart, cart_error = _get_cart(DEFAULT_CUSTOMER_ID)

    metrics = {
        'book_count': len(books),
        'review_count': len(review_data) if isinstance(review_data, list) else 0,
        'cart_items': sum(int(i.get('quantity', 0)) for i in (cart or {}).get('items', [])),
    }

    return render(
        request,
        'home.html',
        {
            **_common_context(DEFAULT_CUSTOMER_ID),
            'metrics': metrics,
            'book_error': book_error,
            'review_error': review_error,
            'cart_error': cart_error,
        },
    )


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

    return render(
        request,
        'books.html',
        {
            **_common_context(DEFAULT_CUSTOMER_ID),
            'books': books,
            'error': error,
            'q': request.GET.get('q', ''),
            'sort': sort,
        },
    )


def book_detail_view(request, book_id):
    book, error = _get_book(book_id)
    reviews = []
    recommendations = []

    _, review_data, review_error = _request('GET', f"{SERVICES['review']}/reviews/book/{book_id}/")
    if isinstance(review_data, list):
        reviews = review_data[:5]

    _, rec_data, rec_error = _request('GET', f"{SERVICES['recommend']}/recommendations/")
    if isinstance(rec_data, dict):
        recommendations = rec_data.get('recommendations', [])[:4]

    return render(
        request,
        'book_detail.html',
        {
            **_common_context(DEFAULT_CUSTOMER_ID),
            'book': book,
            'error': error,
            'reviews': reviews,
            'review_error': review_error,
            'recommendations': recommendations,
            'rec_error': rec_error,
            'add_form': AddToCartForm(initial={'customer_id': DEFAULT_CUSTOMER_ID, 'book_id': book_id, 'quantity': 1, 'next': request.path}),
        },
    )


def cart_add_view(request):
    if request.method != 'POST':
        return redirect('books')

    form = AddToCartForm(request.POST)
    next_url = request.POST.get('next') or f"/cart/{DEFAULT_CUSTOMER_ID}/"
    if not form.is_valid():
        messages.error(request, 'Dữ liệu thêm giỏ hàng không hợp lệ.')
        return redirect(next_url)

    payload = {
        'customer_id': form.cleaned_data['customer_id'],
        'book_id': form.cleaned_data['book_id'],
        'quantity': form.cleaned_data['quantity'],
    }
    status, data, error = _request('POST', f"{SERVICES['cart']}/cart-items/", json=payload)
    if error or status not in (200, 201):
        messages.error(request, f'Add to cart failed: {error or data}')
    else:
        messages.success(request, 'Đã thêm sách vào giỏ hàng.')
    return redirect(next_url)


def cart_view(request, customer_id):
    cart, error = _get_cart(customer_id)
    enriched_items, total_items, total_amount = ([], 0, Decimal('0'))
    if cart:
        enriched_items, total_items, total_amount = _enrich_cart(cart)

    return render(
        request,
        'cart.html',
        {
            **_common_context(customer_id),
            'customer_id': customer_id,
            'cart': cart,
            'items': enriched_items,
            'total_items': total_items,
            'total_amount': total_amount,
            'error': error,
        },
    )


def cart_item_update_view(request, item_id):
    if request.method != 'POST':
        return redirect(f'/cart/{DEFAULT_CUSTOMER_ID}/')

    customer_id = int(request.POST.get('customer_id', DEFAULT_CUSTOMER_ID))
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
    return redirect(f'/cart/{customer_id}/')


def cart_item_delete_view(request, item_id):
    if request.method != 'POST':
        return redirect(f'/cart/{DEFAULT_CUSTOMER_ID}/')

    customer_id = int(request.POST.get('customer_id', DEFAULT_CUSTOMER_ID))
    status, data, error = _request('DELETE', f"{SERVICES['cart']}/cart-items/{item_id}/")
    if error or status not in (200, 202, 204):
        messages.error(request, f'Remove item failed: {error or data}')
    else:
        messages.success(request, 'Đã xóa item khỏi giỏ hàng.')
    return redirect(f'/cart/{customer_id}/')


def checkout_view(request):
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            payload = form.cleaned_data
            status, data, error = _request('POST', f"{SERVICES['order']}/orders/", json=payload)
            request.session['order_result'] = data or {'error': error}
            request.session['order_status_code'] = status or 503
            if error or status not in (200, 201):
                messages.error(request, f'Tạo order thất bại: {error or data}')
            else:
                messages.success(request, 'Tạo order thành công.')
            return redirect('order-result')
    else:
        form = CheckoutForm(initial={'customer_id': DEFAULT_CUSTOMER_ID})

    cart, cart_error = _get_cart(DEFAULT_CUSTOMER_ID)
    items, total_items, total_amount = ([], 0, Decimal('0'))
    if cart:
        items, total_items, total_amount = _enrich_cart(cart)

    return render(
        request,
        'checkout.html',
        {
            **_common_context(DEFAULT_CUSTOMER_ID),
            'form': form,
            'items': items,
            'total_items': total_items,
            'total_amount': total_amount,
            'cart_error': cart_error,
        },
    )


def order_result_view(request):
    result = request.session.get('order_result') or {}
    status_code = request.session.get('order_status_code', 200)
    success = isinstance(status_code, int) and 200 <= status_code < 300
    return render(
        request,
        'order_result.html',
        {
            **_common_context(DEFAULT_CUSTOMER_ID),
            'result': result,
            'status_code': status_code,
            'success': success,
            'items': result.get('items', []) if isinstance(result, dict) else [],
        },
    )


def reviews_view(request, book_id):
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            payload = {
                'customer_id': form.cleaned_data['customer_id'],
                'book_id': book_id,
                'rating': form.cleaned_data['rating'],
                'comment': form.cleaned_data['comment'],
            }
            status, data, error = _request('POST', f"{SERVICES['review']}/reviews/", json=payload)
            if error or status not in (200, 201):
                messages.error(request, f'Gửi review thất bại: {error or data}')
            else:
                messages.success(request, 'Gửi review thành công.')
            return redirect(f'/reviews/book/{book_id}/')
    else:
        form = ReviewForm(initial={'customer_id': DEFAULT_CUSTOMER_ID})

    book, book_error = _get_book(book_id)
    _, reviews, review_error = _request('GET', f"{SERVICES['review']}/reviews/book/{book_id}/")
    reviews = reviews if isinstance(reviews, list) else []
    avg_rating = round(sum(r.get('rating', 0) for r in reviews) / len(reviews), 2) if reviews else 0

    return render(
        request,
        'reviews.html',
        {
            **_common_context(DEFAULT_CUSTOMER_ID),
            'book': book,
            'book_error': book_error,
            'reviews': reviews,
            'review_error': review_error,
            'avg_rating': avg_rating,
            'form': form,
        },
    )


def recommendations_view(request):
    _, payload, error = _request('GET', f"{SERVICES['recommend']}/recommendations/")
    recs = payload.get('recommendations', []) if isinstance(payload, dict) else []

    for r in recs:
        if isinstance(r.get('book'), dict):
            r['book']['display_image'] = _book_image(r['book'])
            r['reason'] = f"Avg rating {r.get('avg_rating', 0)} từ {r.get('review_count', 0)} review"

    return render(
        request,
        'recommendations.html',
        {**_common_context(DEFAULT_CUSTOMER_ID), 'recommendations': recs, 'error': error},
    )


def admin_lite_view(request):
    book_form = AddBookForm(prefix='book')
    customer_form = AddCustomerForm(prefix='customer')

    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type == 'book':
            book_form = AddBookForm(request.POST, prefix='book')
            if book_form.is_valid():
                payload = book_form.cleaned_data
                status, data, error = _request('POST', f"{SERVICES['book']}/books/", json=payload)
                if error or status not in (200, 201):
                    messages.error(request, f'Tạo book thất bại: {error or data}')
                else:
                    messages.success(request, 'Đã tạo book mới.')
                    return redirect('admin-lite')
        elif form_type == 'customer':
            customer_form = AddCustomerForm(request.POST, prefix='customer')
            if customer_form.is_valid():
                payload = customer_form.cleaned_data
                status, data, error = _request('POST', f"{SERVICES['customer']}/customers/", json=payload)
                if error or status not in (200, 201):
                    messages.error(request, f'Tạo customer thất bại: {error or data}')
                else:
                    messages.success(request, 'Đã tạo customer mới (cart sẽ tự tạo).')
                    return redirect('admin-lite')

    service_links = {
        'book-service': 'http://localhost:8005/books/',
        'customer-service': 'http://localhost:8003/customers/',
        'cart-service': f'http://localhost:8006/carts/{DEFAULT_CUSTOMER_ID}/',
        'order-service': 'http://localhost:8007/orders/',
        'review-service': 'http://localhost:8010/reviews/',
    }

    return render(
        request,
        'admin_lite.html',
        {
            **_common_context(DEFAULT_CUSTOMER_ID),
            'book_form': book_form,
            'customer_form': customer_form,
            'service_links': service_links,
        },
    )
