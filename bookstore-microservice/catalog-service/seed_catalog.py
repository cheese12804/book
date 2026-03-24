import os
import time

import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.models import Catalog, CatalogBook  # noqa: E402

CATALOGS = [
    {
        'name': 'Backend Engineering',
        'description': 'Books for backend, API, architecture and microservices.',
        'book_ids': [1, 2, 4, 9, 10],
    },
    {
        'name': 'System & Design',
        'description': 'System design and scalable software books.',
        'book_ids': [5, 6, 7, 8],
    },
]


def wait_book_service(book_id: int, retries: int = 30, delay: float = 2.0) -> bool:
    url = f'http://book-service:8000/books/{book_id}/'
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return True
            print(f'[seed_catalog] book {book_id} check attempt {attempt} got {response.status_code}')
        except requests.RequestException as exc:
            print(f'[seed_catalog] book-service attempt {attempt} error: {exc}')
        time.sleep(delay)
    return False


def main() -> None:
    for data in CATALOGS:
        catalog, created = Catalog.objects.get_or_create(
            name=data['name'],
            defaults={'description': data['description']},
        )
        if not created and catalog.description != data['description']:
            catalog.description = data['description']
            catalog.save(update_fields=['description'])

        print(f'[seed_catalog] catalog_id={catalog.id} name={catalog.name} created={created}')

        for book_id in data['book_ids']:
            if wait_book_service(book_id):
                _, linked = CatalogBook.objects.get_or_create(catalog=catalog, book_id=book_id)
                print(f'[seed_catalog] link catalog={catalog.id} book={book_id} created={linked}')
            else:
                print(f'[seed_catalog] skip missing book_id={book_id}')


if __name__ == '__main__':
    main()
