# from jose import jwt
# from datetime import datetime, timedelta

# SECRET_KEY = "aurfx_secret_key"

# ALGORITHM = "HS256"

# ACCESS_TOKEN_EXPIRE_MINUTES = 60


# def create_access_token(data: dict):

#     to_encode = data.copy()

#     expire = datetime.utcnow() + timedelta(
#         minutes=ACCESS_TOKEN_EXPIRE_MINUTES
#     )

#     to_encode.update({"exp": expire})

#     encoded_jwt = jwt.encode(
#         to_encode,
#         SECRET_KEY,
#         algorithm=ALGORITHM
#     )

#     return encoded_jwt
from jose import jwt, JWTError
from datetime import datetime, timedelta

SECRET_KEY = "aurfx_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({
        "exp": expire
    })

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def decode_access_token(token: str):
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
    except JWTError:
        return None