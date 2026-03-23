import requests
from django.shortcuts import redirect, render


DEFAULT_TIMEOUT = 8


def _safe_get_json(url, default):
    try:
        response = requests.get(url, timeout=DEFAULT_TIMEOUT)
        if response.status_code == 200:
            return response.json(), None
        return default, f'GET {url} returned {response.status_code}'
    except requests.RequestException as exc:
        return default, str(exc)


def books_view(request):
    books, error = _safe_get_json('http://book-service:8000/books/', [])
    return render(request, 'books.html', {'books': books, 'error': error})


def cart_view(request, customer_id):
    cart, error = _safe_get_json(f'http://cart-service:8000/carts/{customer_id}/', None)
    return render(request, 'cart.html', {'cart': cart, 'customer_id': customer_id, 'error': error})


def order_create_view(request):
    if request.method == 'POST':
        payload = {
            'customer_id': request.POST.get('customer_id'),
            'pay_method': request.POST.get('pay_method'),
            'ship_method': request.POST.get('ship_method'),
            'shipping_address': request.POST.get('shipping_address'),
        }
        try:
            response = requests.post('http://order-service:8000/orders/', json=payload, timeout=DEFAULT_TIMEOUT)
            request.session['order_result'] = response.json()
            request.session['order_status_code'] = response.status_code
        except requests.RequestException as exc:
            request.session['order_result'] = {'error': 'order-service unavailable', 'detail': str(exc)}
            request.session['order_status_code'] = 503
        return redirect('/orders/result/')
    return render(request, 'order_form.html')


def order_result_view(request):
    result = request.session.get('order_result', {})
    status_code = request.session.get('order_status_code', 200)
    return render(request, 'order_result.html', {'result': result, 'status_code': status_code})


def reviews_by_book_view(request, book_id):
    reviews, error = _safe_get_json(f'http://comment-rate-service:8000/reviews/book/{book_id}/', [])
    return render(request, 'reviews.html', {'reviews': reviews, 'book_id': book_id, 'error': error})


def recommendations_view(request):
    payload, error = _safe_get_json('http://recommender-ai-service:8000/recommendations/', {'recommendations': []})
    recommendations = payload.get('recommendations', []) if isinstance(payload, dict) else []
    return render(request, 'recommendations.html', {'recommendations': recommendations, 'error': error})
