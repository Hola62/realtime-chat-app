from flask_jwt_extended import create_access_token


def generate_token(user_id: int) -> str:
    """Wrap create_access_token to keep import sites minimal."""
    return create_access_token(identity=str(user_id))
