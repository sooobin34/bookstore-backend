from marshmallow import Schema, fields

class ErrorSchema(Schema):
    status = fields.Integer(required=True)
    code = fields.String(required=True)
    message = fields.String(required=True)
    path = fields.String()
    timestamp = fields.String()
    details = fields.Dict()
