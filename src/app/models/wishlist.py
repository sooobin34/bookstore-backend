from ..extensions import db

class Wishlist(db.Model):
    __tablename__ = "wishlists"

    wishlist_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.book_id"), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    book = db.relationship("Book", backref="wishlists", lazy="selectin")
    user = db.relationship("User", backref="wishlists", lazy="selectin")