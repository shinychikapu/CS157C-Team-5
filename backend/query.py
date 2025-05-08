from contextlib import asynccontextmanager
from neo4j import GraphDatabase
from dotenv import load_dotenv
from extractor import extractor
import os

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)
def queryDB(text):
    session = driver.session()
    try:
        # 1) Extract ingredients & tags
        extraction  = extractor(text)
        ingredients = [i.lower() for i in extraction.get("ingredients", [])]
        tags        = [t.lower() for t in extraction.get("tags", [])]
        if len(tags) == 0:
            print(0)
            cypher = """
WITH $ingredients AS wantIng

//Find Recipe with required Ingredients
MATCH (r:Recipe)-[:HAS_INGREDIENT]->(ing:Ingredient)
WITH r, collect(DISTINCT toLower(ing.name)) AS allIng, wantIng
WHERE all(req IN wantIng 
          WHERE any(real IN allIng WHERE real STARTS WITH req))

// Compute Extra Ingredients
WITH r, allIng, size(allIng) - size(wantIng) AS ingredientExtras

RETURN r {
  .name,
  .description,
  ingredients:    allIng,
  tags:           r.tags,
  steps:          r.steps,
  ingredientExtras: ingredientExtras
} AS recipe
ORDER BY ingredientExtras ASC
LIMIT 10;
"""
        else:
            print(1)
            cypher = """
WITH $ingredients AS wantIng, $tags AS wantTags

//Find recipe with required Ingredients
MATCH (r:Recipe)-[:HAS_INGREDIENT]->(ing:Ingredient)
WITH 
  r,
  collect(DISTINCT toLower(ing.name)) AS allIng,
  wantIng,
  wantTags
WHERE all(req IN wantIng 
          WHERE any(act IN allIng WHERE act STARTS WITH req))

// Filter by tags
  AND all(tagReq IN wantTags 
          WHERE exists {
            MATCH (r)-[:HAS_TAG]->(t:Tag)
            WHERE toLower(t.tags) = tagReq
          })

//Compute extra ingredients
WITH 
  r, 
  allIng, 
  size(allIng) - size(wantIng) AS ingredientExtras

//get all tags of recipe
OPTIONAL MATCH (r)-[:HAS_TAG]->(tAll:Tag)
WITH 
  r, 
  allIng, 
  ingredientExtras, 
  collect(DISTINCT tAll.tags) AS allTags

//sort by fewest extra ingredients
RETURN r {
  .name,
  .description,
  ingredients:    allIng,
  tags:           allTags,
  steps:          r.steps
} AS recipe
ORDER BY ingredientExtras ASC
LIMIT 10;
"""
        params = {"ingredients": ingredients, "tags": tags}
        result  = session.run(cypher, params)
        recipes = [record["recipe"] for record in result]
        if not recipes:
            return None
        return recipes[0]

    except Exception as e:
        return {"error": str(e)}

    finally:
        session.close()

    
print(queryDB("I have pork and egg. What Asian dish can I make under 30 minutes?")) 