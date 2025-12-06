# src/app/schemas/wishlist.py

from marshmallow import Schema, fields


class WishlistCreateSchema(Schema):
    """
    위시리스트에 책을 추가할 때 사용하는 요청 바디 스키마
    예:
    {
      "book_id": 3
    }
    """
    book_id = fields.Int(
        required=True,
        metadata={"description": "추가할 도서의 ID"},
    )


class WishlistItemSchema(Schema):
    """
    위시리스트 아이템 응답용 스키마
    """
    wishlist_id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    book_id = fields.Int(required=True)
    created_at = fields.DateTime(dump_only=True)

