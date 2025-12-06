import random
from faker import Faker

from src.app import create_app
from src.app.extensions import db
from src.app.models import User, Book, Review, Order, OrderItem, CartItem, Wishlist
from src.app.security import hash_password

fake = Faker()


def seed_users(n=30):
    users = []

    # 기본 admin 계정 1개
    admin = User(
        name="Admin User",
        email="admin@example.com",
        password=hash_password("Admin123!"),  # 이 비번으로 로그인 가능
        role="ADMIN",
    )
    db.session.add(admin)
    users.append(admin)

    # 일반 유저 n명
    for _ in range(n):
        user = User(
            name=fake.name(),
            email=fake.unique.email(),
            password=hash_password("User123!"),  # 전부 같은 비번이라도 상관 없음
            role="USER",
        )
        users.append(user)
        db.session.add(user)

    db.session.commit()
    return users


def seed_books(n=60):
    books = []
    for _ in range(n):
        book = Book(
            title=fake.sentence(nb_words=3),
            author=fake.name(),
            category=random.choice(["Fiction", "Tech", "History", "Art", "Science"]),
            price=round(random.uniform(5, 100), 2),
            stock=random.randint(10, 100),
            is_bestseller=random.choice([True, False]),
            description=fake.text(max_nb_chars=200),
            image_url=fake.image_url()
        )
        books.append(book)
        db.session.add(book)
    db.session.commit()
    return books


def seed_reviews(users, books, n=100):
    for _ in range(n):
        review = Review(
            user_id=random.choice(users).user_id,
            book_id=random.choice(books).book_id,
            rating=random.randint(1, 5),
            content=fake.text(max_nb_chars=150),
            likes_count=random.randint(0, 50),
        )
        db.session.add(review)
    db.session.commit()


def seed_orders(users, books, n=50):
    orders = []

    for _ in range(n):
        user = random.choice(users)
        # 우선 주문 객체만 만들고 세션에 올림
        order = Order(
            user_id=user.user_id,
            total_price=0,
            status=random.choice(["pending", "completed"]),
        )
        db.session.add(order)

        # order_id를 바로 쓰기 위해 flush
        db.session.flush()

        total_price = 0

        # 주문 항목 1~3개 생성
        for _ in range(random.randint(1, 3)):
            book = random.choice(books)
            quantity = random.randint(1, 3)
            price = float(book.price)

            item = OrderItem(
                order_id=order.order_id,
                book_id=book.book_id,
                quantity=quantity,
                price=price,
            )
            db.session.add(item)

            total_price += price * quantity

        order.total_price = total_price
        orders.append(order)

    # 한 번에 커밋
    db.session.commit()
    print("✅ orders seeded:", len(orders))
    print("✅ DB orders count:", Order.query.count())

    return orders



def seed_cart_wishlist(users, books):
    for user in users:
        # Cart items
        for _ in range(random.randint(0, 3)):
            cart = CartItem(
                user_id=user.user_id,
                book_id=random.choice(books).book_id,
                quantity=random.randint(1, 3)
            )
            db.session.add(cart)

        # Wishlist
        for _ in range(random.randint(0, 3)):
            wl = Wishlist(
                user_id=user.user_id,
                book_id=random.choice(books).book_id,
            )
            db.session.add(wl)

    db.session.commit()


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        print("🌱 Seeding users...")
        users = seed_users()

        print("🌱 Seeding books...")
        books = seed_books()

        print("🌱 Seeding reviews...")
        seed_reviews(users, books)

        print("🌱 Seeding orders & order_items...")
        seed_orders(users, books)

        print("🌱 Seeding cart_items & wishlists...")
        seed_cart_wishlist(users, books)

        print("🎉 Seeding complete!")
