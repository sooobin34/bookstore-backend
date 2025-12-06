from marshmallow import Schema, fields

class ReviewSchema(Schema):
    review_id = fields.Integer()
    user_id = fields.Integer()
    book_id = fields.Integer()
    rating = fields.Integer()
    content = fields.String()
    created_at = fields.String()
