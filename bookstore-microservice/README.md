# BookStore Microservice - Assignment 05

## 1. Giới thiệu hệ thống
Hệ thống BookStore được tách từ monolith thành 12 microservice độc lập dùng Django REST Framework, giao tiếp REST nội bộ qua Docker network.

## 2. Danh sách 12 microservices
1. staff-service
2. manager-service
3. customer-service
4. catalog-service
5. book-service
6. cart-service
7. order-service
8. ship-service
9. pay-service
10. comment-rate-service
11. recommender-ai-service
12. api-gateway

## 3. Sơ đồ kiến trúc (luồng chính)
- customer-service -> cart-service (auto tạo cart)
- book-service -> staff-service (validate staff)
- catalog-service -> book-service (validate book)
- cart-service -> book-service (validate book)
- order-service -> customer-service, cart-service, book-service, pay-service, ship-service
- comment-rate-service -> customer-service, book-service
- recommender-ai-service -> comment-rate-service, book-service
- api-gateway -> các service để render trang demo

## 4. Cách chạy bằng Docker Compose
```bash
cd bookstore-microservice
docker compose up --build
```

## 5. Các lệnh migrate
Có 2 cách:

### Cách 1 (tự động trong Dockerfile CMD)
Khi `docker compose up`, mỗi service tự chạy `python manage.py makemigrations app` và `python manage.py migrate`.

### Cách 2 (manual)
```bash
docker compose run --rm staff-service python manage.py migrate
docker compose run --rm manager-service python manage.py migrate
docker compose run --rm customer-service python manage.py migrate
docker compose run --rm catalog-service python manage.py migrate
docker compose run --rm book-service python manage.py migrate
docker compose run --rm cart-service python manage.py migrate
docker compose run --rm order-service python manage.py migrate
docker compose run --rm ship-service python manage.py migrate
docker compose run --rm pay-service python manage.py migrate
docker compose run --rm comment-rate-service python manage.py migrate
docker compose run --rm recommender-ai-service python manage.py migrate
docker compose run --rm api-gateway python manage.py migrate
```


## Seed data tự động
- `staff-service`: load `app/fixtures/staffs.json` (2 staff).
- `manager-service`: load `app/fixtures/managers.json` (1 manager).
- `book-service`: load `app/fixtures/books.json` (10 books).
- `customer-service`: chạy `seed_customer.py` tạo 2 customer và gọi `cart-service` tạo cart tương ứng.
- `catalog-service`: chạy `seed_catalog.py` tạo 2 catalog và gán book bằng validate qua `book-service`.
- `comment-rate-service`: load `app/fixtures/reviews.json` (>=5 review).
- `cart-service`, `order-service`: không seed trực tiếp (theo flow nghiệp vụ).

## 6. Danh sách endpoint chính
- staff-service: `/staffs/`, `/staffs/<id>/`
- manager-service: `/managers/`, `/managers/<id>/`
- customer-service: `/customers/`, `/customers/<id>/`
- catalog-service: `/catalogs/`, `/catalogs/<id>/`, `/catalogs/<id>/books/`, `/catalogs/<id>/books/`
- book-service: `/books/`, `/books/<id>/`
- cart-service: `/carts/`, `/carts/<customer_id>/`, `/cart-items/`, `/cart-items/<id>/ (PUT/DELETE)`
- order-service: `/orders/`, `/orders/<id>/`
- ship-service: `/shipments/`, `/shipments/<id>/`
- pay-service: `/payments/`, `/payments/<id>/`
- comment-rate-service: `/reviews/`, `/reviews/book/<book_id>/`, `/reviews/customer/<customer_id>/`
- recommender-ai-service: `/recommendations/`, `/recommendations/customer/<customer_id>/`
- api-gateway: `/books/`, `/cart/<customer_id>/`, `/orders/create/`, `/orders/result/`, `/reviews/book/<book_id>/`, `/recommendations/`

## 7. Kịch bản demo
1. Tạo staff
2. Tạo manager
3. Tạo customer
4. Verify cart tự động tạo
5. Staff thêm book (có created_by_staff_id)
6. Tạo catalog và gán sách vào catalog
7. Customer thêm book vào cart
8. Xem cart
9. Tạo order
10. Kiểm tra payment + shipping tạo tự động
11. Customer đánh giá book
12. Xem recommendation
13. Mở giao diện api-gateway để demo UI

## 8. Gợi ý phân chia công việc cho nhóm
- Nhóm A: staff/manager/customer
- Nhóm B: book/catalog/cart
- Nhóm C: order/pay/ship
- Nhóm D: comment-rate/recommender/api-gateway + tích hợp compose


## Verify seed nhanh
```bash
curl http://localhost:8005/books/
curl http://localhost:8003/customers/
curl http://localhost:8006/carts/1/
curl http://localhost:8006/carts/2/
curl http://localhost:8004/catalogs/
curl http://localhost:8010/reviews/
```

## Ví dụ nhanh endpoint
```bash
# 1) create staff
curl -X POST http://localhost:8001/staffs/ -H 'Content-Type: application/json' -d '{"name":"Alice","email":"alice@book.com","department":"content"}'

# 2) create manager
curl -X POST http://localhost:8002/managers/ -H 'Content-Type: application/json' -d '{"name":"Bob","email":"bob@book.com"}'

# 3) create customer (auto create cart)
curl -X POST http://localhost:8003/customers/ -H 'Content-Type: application/json' -d '{"name":"Carol","email":"carol@book.com","address":"HCM"}'

# 4) create book
curl -X POST http://localhost:8005/books/ -H 'Content-Type: application/json' -d '{"title":"Django 101","author":"Author A","price":"10.50","stock":100,"created_by_staff_id":1}'

# 5) add cart item
curl -X POST http://localhost:8006/cart-items/ -H 'Content-Type: application/json' -d '{"customer_id":1,"book_id":1,"quantity":2}'

# 6) create order
curl -X POST http://localhost:8007/orders/ -H 'Content-Type: application/json' -d '{"customer_id":1,"pay_method":"COD","ship_method":"FAST","shipping_address":"123 Street"}'

# 7) review
curl -X POST http://localhost:8010/reviews/ -H 'Content-Type: application/json' -d '{"customer_id":1,"book_id":1,"rating":5,"comment":"Great"}'

# 8) recommendations
curl http://localhost:8011/recommendations/
```
