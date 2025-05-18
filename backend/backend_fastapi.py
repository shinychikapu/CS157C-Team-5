from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from response import queryDB, format_recipe, polish_markdown
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
import uvicorn
import os
from neo4j import GraphDatabase
import torch
import uuid
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

device = 0 if torch.cuda.is_available() else -1

flan_large = "google/flan-t5-large"
tok_fl   = AutoTokenizer.from_pretrained(flan_large)
model_fl = AutoModelForSeq2SeqLM.from_pretrained(flan_large).to(
    f"cuda:{device}" if device>=0 else "cpu"
)

# Tag Classification model
tag_model = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli",
    device=device,
    multi_label=True,
)

# LLM for ingredients extraction
gen_model = pipeline(
    "text2text-generation",
    model=model_fl,
    tokenizer=tok_fl,
    device=device,
)
sessions: Dict[str, Dict[str, Any]] = {}

class UserIn(BaseModel):
    email: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str

class QueryIn(BaseModel):
    question: str

class SessionIn(BaseModel):
    session_id: str

class RecipeSessionOut(BaseModel):
    session_id: str
    markdown:   str
    total:      int
    index:      int
    recipes:    List[dict]

class SaveRecipeIn(BaseModel):
    recipe_id: int

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
    print("Log in")
    record = get_user_record(user.email)
    if not record or not verify_password(user.password, record["hashed_password"]):
        raise HTTPException(401, "Invalid email or password")
    token = create_access_token(record["email"])
    return {"access_token": token, "token_type": "bearer"}

@app.post("/api/recipe", response_model=RecipeSessionOut)
def start_recipe(q: QueryIn):
    all_recipes = queryDB(q.question, driver, gen_model, tag_model)
    if not all_recipes:
        raise HTTPException(404, "No recipes found")

    # new session
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "recipes": all_recipes,
        "index": 0
    }

    # format the first recipe
    raw      = all_recipes[0]
    plain_md = format_recipe(raw)
    md       = polish_markdown(plain_md)
    print(md)
    return RecipeSessionOut(
        session_id=session_id,
        markdown=md,
        total=len(all_recipes),
        index=0,
        recipes = all_recipes
    )

@app.post("/api/recipe/next", response_model=RecipeSessionOut)
def next_recipe(s: SessionIn):
    sess = sessions.get(s.session_id)
    if not sess:
        raise HTTPException(404, "Session not found")

    recipes = sess["recipes"]
    # advance index but cap at last
    sess["index"] = min(sess["index"] + 1, len(recipes) - 1)
    idx = sess["index"]

    raw      = recipes[idx]
    plain_md = format_recipe(raw)
    md       = polish_markdown(plain_md)
    print(md)
    return RecipeSessionOut(
        session_id=s.session_id,
        markdown=md,
        total=len(recipes),
        index=idx,
        recipes=recipes
    )

@app.post("/api/user/save-recipe")
def save_recipe(
    payload: SaveRecipeIn,
    current_user_email: str = Depends(get_current_user),
):
    """
    current_user_email will be the `sub` field from the JWT if
    the token was valid.  Otherwise FastAPI will immediately return 401.
    """
    recipe_id = payload.recipe_id
    print(recipe_id)
    # now persist the SAVED relationship in Neo4j
    with driver.session() as session:
        session.run(
            """
            MATCH (u:User {email:$email})
            MATCH (r:Recipe {id:$recipe_id})
            MERGE (u)-[:SAVED]->(r)
            """,
            {"email": current_user_email, "recipe_id": recipe_id}
        )

    return {"status": "ok", "recipe_saved": recipe_id}

@app.get("/api/user/saved-recipes", dependencies=[Depends(get_current_user)])
def get_saved_recipes(current_user: str = Depends(get_current_user)):
    with driver.session() as session:
        result = session.run("""
            MATCH (u:User {email: $email})-[:SAVED]->(r:Recipe)
            RETURN r { .id, .name, .description, steps: r.steps } AS recipe
        """, {"email": current_user})
        recipes = [rec["recipe"] for rec in result]
    return {"recipes": recipes}

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
