from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from jose import jwt

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = "tu_clave_secreta"
ALGORITHM = "HS256"

FAKE_USER = {
    "username": "admin",
    "password": "1234"
}

@router.post("/login")
def login(username: str, password: str):
    if username != FAKE_USER["username"] or password != FAKE_USER["password"]:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token = jwt.encode(
        {
            "sub": username,
            "exp": datetime.utcnow() + timedelta(hours=8)
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return {"access_token": token}