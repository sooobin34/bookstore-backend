# src/app/models/__init__.py

from src.app.extensions import db

from .user import User
from .book import Book
from .review import Review
from .wishlist import Wishlist

# Cart / Order / OrderItem 은 이 파일들에서만 가져온다!
from .cart import CartItem
from .order import Order, OrderItem

__all__ = [
    "db",
    "User",
    "Book",
    "Review",
    "Wishlist",
    "CartItem",
    "Order",
    "OrderItem",
]
