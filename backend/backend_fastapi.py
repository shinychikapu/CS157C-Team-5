from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend.response import queryDB, format_recipe, polish_markdown
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "123456789")
)

app = FastAPI()

class QueryIn(BaseModel):
    question: str

class RecipeOut(BaseModel):
    markdown: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/recipe", response_model=RecipeOut)
def get_recipe(q: QueryIn):
    recipes = queryDB(q.question, driver)      
    if not recipes:
        raise HTTPException(status_code=404, detail="No recipes found")
    raw = recipes[0]
    plain_md = format_recipe(raw)
    final_md = polish_markdown(plain_md)
    print(final_md)
    return RecipeOut(markdown=final_md)

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
