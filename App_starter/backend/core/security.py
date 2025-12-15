from jose import JWTError, jwt
from pydantic import BaseModel


class TokenData(BaseModel):
    sub: str | None = None


def decode_token(token: str, secret: str) -> TokenData:
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return TokenData(sub=payload.get("sub"))
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
