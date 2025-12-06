from marshmallow import Schema, fields

class OrderItemSchema(Schema):
    order_item_id = fields.Integer()
    book_id = fields.Integer()
    quantity = fields.Integer()
    price = fields.Float()

class OrderSchema(Schema):
    order_id = fields.Integer()
    user_id = fields.Integer()
    total_price = fields.Float()
    status = fields.String()
    items = fields.List(fields.Nested(OrderItemSchema))
    created_at = fields.String()

class OrderCreateSchema(Schema):
    address = fields.String(required=False)  # 필요시 확장
