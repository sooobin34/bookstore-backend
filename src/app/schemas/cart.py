from marshmallow import Schema, fields

class CartItemSchema(Schema):
    cart_item_id = fields.Integer()
    user_id = fields.Integer()
    book_id = fields.Integer()
    quantity = fields.Integer()
    created_at = fields.String()

class CartCreateSchema(Schema):
    book_id = fields.Integer(required=True)
    quantity = fields.Integer(required=True)
