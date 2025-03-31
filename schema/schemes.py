from marshmallow import Schema, fields, ValidationError

class LoginSchema(Schema):
    key = fields.Str(required=True, error_messages={"required": "Key is required."})
    hwid = fields.Str(required=True, error_messages={"required": "HWID is required."})

class KeyAddSchema(Schema):
    admin = fields.Str(required=True, validate=lambda x: x == "admin", error_messages={"invalid": "Invalid admin value."})
    password = fields.Str(required=True, validate=lambda x: x == "intokeybd", error_messages={"invalid": "Invalid password."})
    keys = fields.Str(required=True, error_messages={"required": "Keys are required."})

class CheckVersionProgramScheme(Schema):
    version = fields.Str(required=True, error_messages={"invalid": "Invalid version value."})