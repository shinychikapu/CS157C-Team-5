# reference https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/

from neo4j import GraphDatabase
from passlib.context import CryptContext
import os, jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "123456789")
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def get_user_record(email: str):
    with driver.session() as session:
        result = session.run(
            "MATCH (u:User {email: $email}) RETURN u.email AS email, u.hashed_password AS hashed_password",
            {"email": email}
        )
        return result.single()

def create_user_record(email: str, hashed_password: str):
    with driver.session() as session:
        session.run(
            "CREATE (u:User {email: $email, hashed_password: $hashed_password})",
            {"email": email, "hashed_password": hashed_password}
        )

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(sub: str, expires_delta: timedelta | None = None):
    to_encode = {"sub": sub}
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(401, "Invalid credentials")
        if not get_user_record(email):
            raise HTTPException(401, "User no longer exists")
        return email
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid credentials")