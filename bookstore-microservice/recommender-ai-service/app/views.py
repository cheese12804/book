import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


def _fetch_books():
    response = requests.get('http://book-service:8000/books/', timeout=5)
    response.raise_for_status()
    return response.json()


def _fetch_reviews():
    response = requests.get('http://comment-rate-service:8000/reviews/', timeout=5)
    response.raise_for_status()
    return response.json()


class RecommendationView(APIView):
    def get(self, request):
        try:
            books = _fetch_books()
            reviews = _fetch_reviews()
        except requests.RequestException as exc:
            return Response({'error': 'Dependency unavailable', 'detail': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        rating_map = {}
        count_map = {}
        for r in reviews:
            book_id = r.get('book_id')
            rating_map[book_id] = rating_map.get(book_id, 0) + int(r.get('rating', 0))
            count_map[book_id] = count_map.get(book_id, 0) + 1

        scored = []
        for book in books:
            bid = book['id']
            count = count_map.get(bid, 0)
            avg = rating_map.get(bid, 0) / count if count else 0
            scored.append({'book': book, 'avg_rating': round(avg, 2), 'review_count': count})

        scored.sort(key=lambda x: (x['avg_rating'], x['review_count']), reverse=True)
        if not any(item['review_count'] for item in scored):
            scored = scored[:5]
        else:
            scored = scored[:5]

        return Response({'recommendations': scored})


class RecommendationByCustomerView(APIView):
    def get(self, request, customer_id):
        try:
            all_reviews = _fetch_reviews()
            books = _fetch_books()
        except requests.RequestException as exc:
            return Response({'error': 'Dependency unavailable', 'detail': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        reviewed_book_ids = {r['book_id'] for r in all_reviews if r.get('customer_id') == customer_id}
        candidates = [b for b in books if b['id'] not in reviewed_book_ids]
        return Response({'customer_id': customer_id, 'recommendations': candidates[:5]})
