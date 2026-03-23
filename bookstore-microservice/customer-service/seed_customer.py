import os
import time

import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.models import Customer  # noqa: E402

CUSTOMERS = [
    {"name": "Carol Nguyen", "email": "carol.customer@bookstore.com", "address": "123 Nguyen Trai, HCM"},
    {"name": "David Pham", "email": "david.customer@bookstore.com", "address": "88 Le Loi, Da Nang"},
]


def ensure_cart(customer_id: int, retries: int = 30, delay: float = 2.0) -> None:
    url = 'http://cart-service:8000/carts/'
    payload = {"customer_id": customer_id}
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code in (200, 201):
                print(f'[seed_customer] cart ready for customer_id={customer_id}')
                return
            print(f'[seed_customer] cart-service attempt {attempt} returned {response.status_code}: {response.text}')
        except requests.RequestException as exc:
            print(f'[seed_customer] cart-service attempt {attempt} error: {exc}')
        time.sleep(delay)
    raise RuntimeError(f'Failed to create cart for customer_id={customer_id}')


def main() -> None:
    for payload in CUSTOMERS:
        customer, created = Customer.objects.get_or_create(
            email=payload['email'],
            defaults={
                'name': payload['name'],
                'address': payload['address'],
            },
        )
        if not created:
            customer.name = payload['name']
            customer.address = payload['address']
            customer.save(update_fields=['name', 'address'])
        print(f"[seed_customer] customer_id={customer.id} email={customer.email} created={created}")
        ensure_cart(customer.id)


if __name__ == '__main__':
    main()
