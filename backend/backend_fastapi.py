from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from response import queryDB, format_recipe, polish_markdown
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from auth import (
    get_user_record,
    create_user_record,
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "123456789")
)

class UserIn(BaseModel):
    email: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str

class QueryIn(BaseModel):
    question: str

class RecipeOut(BaseModel):
    markdown: str
    recipes: list[dict]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/auth/register", status_code=201)
def register(user: UserIn):
    if get_user_record(user.email):
        raise HTTPException(400, "Email already taken")
    hashed = hash_password(user.password)
    create_user_record(user.email, hashed)
    return {"msg": "User registered"}

# Login
@app.post("/auth/login", response_model=TokenOut)
def login(user: UserIn):
    record = get_user_record(user.email)
    if not record or not verify_password(user.password, record["hashed_password"]):
        raise HTTPException(401, "Invalid email or password")
    token = create_access_token(record["email"])
    return {"access_token": token, "token_type": "bearer"}

@app.post("/api/recipe", response_model=RecipeOut)
def get_recipe(q: QueryIn):
    recipes = queryDB(q.question, driver)
    print(recipes)     
    if not recipes:
        raise HTTPException(status_code=404, detail="No recipes found")
    raw = recipes[0]
    plain_md = format_recipe(raw)
    final_md = polish_markdown(plain_md)
    print(final_md)
    return RecipeOut(markdown=final_md, recipes=recipes)

@asynccontextmanager
async def lifespan(app: FastAPI):
    driver.close()

if __name__ == "__main__":
    uvicorn.run(
        "backend.backend_fastapi:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 4000)),
        reload=True
    )
