from marshmallow import Schema, fields

class UserSignupSchema(Schema):
    name = fields.String(required=True)
    email = fields.Email(required=True)
    password = fields.String(required=True)

class UserLoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True)

class UserMeSchema(Schema):
    user_id = fields.Integer()
    name = fields.String()
    email = fields.String()
    role = fields.String()
