from flask_smorest import Api

from .health import blp as health_blp
from .books import blp as books_blp
from .auth import blp as auth_blp
from .users import blp as users_blp
from .reviews import blp as reviews_blp
from .cart import blp as cart_blp
from .orders import blp as orders_blp
from .wishlist import blp as wishlist_blp

api = Api()


def init_app(app):

    # flask-smorest Api 초기화
    api.init_app(app)

    # Blueprint 등록
    api.register_blueprint(health_blp)
    api.register_blueprint(books_blp)
    api.register_blueprint(auth_blp)
    api.register_blueprint(users_blp)
    api.register_blueprint(reviews_blp)
    api.register_blueprint(cart_blp)
    api.register_blueprint(orders_blp)
    api.register_blueprint(wishlist_blp)