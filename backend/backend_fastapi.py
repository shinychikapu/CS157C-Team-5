import os
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from neo4j import GraphDatabase
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    question: str

@app.post("/api/query")
def queryDB(query: Query):
    session = driver.session()
    try:
        q = query.question.lower()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

@app.get("/api/nodes")
def get_nodes():
    session = driver.session()
    try:
        result = session.run("MATCH (n) RETURN n LIMIT 30")
        nodes = [record["n"]._properties for record in result]
        return nodes
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error querying Neo4j") from e
    finally:
        session.close()

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
