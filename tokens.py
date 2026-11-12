from flask import current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature


class TokenService:

    @staticmethod
    def _serializer(salt):
        return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=salt)

    @staticmethod
    def make(data, salt):
        return TokenService._serializer(salt).dumps(data)

    @staticmethod
    def read(token, salt, max_age):
        try:
            return TokenService._serializer(salt).loads(token, max_age=max_age)
        except BadSignature:  # also covers expired tokens
            return None