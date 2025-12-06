from marshmallow import Schema, fields

class BookSchema(Schema):
    book_id = fields.Integer()
    title = fields.String()
    author = fields.String()
    price = fields.Float()

class BookCreateSchema(Schema):
    title = fields.String(required=True)
    author = fields.String(required=True)
    price = fields.Float(required=True)
