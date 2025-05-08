from transformers import AutoModelForSeq2SeqLM, AutoTokenizer,pipeline
import torch
from neo4j import GraphDatabase
import json
import re
from contextlib import asynccontextmanager
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

device = 0 if torch.cuda.is_available() else -1

flan_large = "google/flan-t5-large"
tok_fl   = AutoTokenizer.from_pretrained(flan_large)
model_fl = AutoModelForSeq2SeqLM.from_pretrained(flan_large).to(
    f"cuda:{device}" if device>=0 else "cpu"
)

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
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

def extract_ingredients(text: str) -> list:
    prompt = f"""
Your job is to extract only the ingredient names from the user’s request.
Respond with a comma-separated list, nothing else. Don't repeat ingredients

Examples:

User: "I want to make a dish with rice, egg, and meat."
Ingredients: rice, egg, meat

User: "I have flour, sugar and butter at home."
Ingredients: flour, sugar, butter

User: "{text}"
Ingredients:
"""
    
    result = gen_model(prompt)[0]["generated_text"].strip()

    if result.lower().startswith("ingredients"):
        _, csv = result.split(":", 1)
    else:
        csv = result


    items = [i.strip() for i in csv.split(",") if i.strip()]

    seen = set()
    unique_items = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique_items.append(item)
    return unique_items





# Tags extraction
POSSIBLE_TAGS = [
 '60-minutes-or-less',
 '30-minutes-or-less',
 '15-minutes-or-less',

 'vegetarian',
 'vegan',
 'gluten-free',
 'dairy-free',
 'nut-free',
 'low-sodium',
 'low-cholesterol',
 'low-carb',
 'low-fat',
 'low-calorie',
 'low-protein',
 'high-protein',

 'american',
 'asian',
 'italian',
 'mexican',
 'french',
 'south-american',
 'middle-eastern',

 'christmas',
 'thanksgiving',
 'easter',
 'halloween',
 'birthday'
]

def extract_tags(text, threshold=0.7):
    out = tag_model(text, POSSIBLE_TAGS)
    return [
        label for label, score in zip(out["labels"], out["scores"])
        if score >= threshold
    ]

def extractor(text):
    ingredients = extract_ingredients(text)
    tags = extract_tags(text)
    return{
        "ingredients": ingredients,
        "tags" : tags
    }

def queryDB(text):
    session = driver.session()
    try:
        # 1) Extract ingredients & tags
        extraction  = extractor(text)
        ingredients = [i.lower() for i in extraction.get("ingredients", [])]
        tags        = [t.lower() for t in extraction.get("tags", [])]
        print(ingredients)
        print(tags)
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
        return recipes

    except Exception as e:
        return {"error": str(e)}

    finally:
        session.close()
def parse_steps(s: str) -> list[str]:
    """
    Given a string like "['step1', 'step2', ...]", split on commas
    and strip quotes, brackets, and whitespace.
    """
    parts = s.split(",")
    cleaned = []
    for part in parts:
        # remove brackets, quotes, and leading/trailing whitespace
        p = part.replace("[", "").replace("]", "").replace("'", "").replace('"', "").strip()
        if p:
            cleaned.append(p)
    return cleaned

def format_recipe_plain(recipe: dict) -> str:
    """
    Safely formats a recipe dict to Markdown, splitting steps properly.
    """
    name        = recipe.get("name", "")
    description = recipe.get("description", "")
    ingredients = recipe.get("ingredients") or []
    # if ingredients came in as a stringified list, parse similarly:
    if isinstance(ingredients, str):
        ingredients = [i.strip().strip("[]'\" ") for i in ingredients.split(",") if i.strip()]

    # parse steps string into a Python list
    steps = recipe.get("steps") or []
    if isinstance(steps, str):
        steps = parse_steps(steps)

    tags = recipe.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip().strip("[]'\" ") for t in tags.split(",") if t.strip()]

    lines = [f"# {name}\n"]

    if description:
        lines.append(f"**Description:** {description}\n")

    lines.append("**Ingredients:**")
    for ing in ingredients:
        lines.append(f"- {ing}")
    lines.append("")

    lines.append("**Steps:**")
    for idx, step in enumerate(steps, 1):
        lines.append(f"{idx}. {step}")
    lines.append("")

    if tags:
        lines.append(f"**Tags:** {', '.join(tags)}")

    return "\n".join(lines)


def format_recipe(recipe: dict) -> str:
    name        = recipe.get("name", "")
    description = recipe.get("description", "")
    ingredients = recipe.get("ingredients", [])
    steps       = parse_steps(recipe.get("steps", []))
    
    lines = []
    # Title
    lines.append(f"# {name}\n")

    # Description
    if description:
        lines.append(f"## Description: {description}\n")

    # Ingredients
    lines.append("## Ingredients:")
    for ing in ingredients:
        lines.append(f"- {ing}")
    lines.append("")  # blank line

    # Steps
    lines.append("## Steps:")
    for  i in range(len(steps)):
        lines.append(f"{i+1}. {steps[i]}")
    lines.append("")  # blank line

    return "\n".join(lines)

def polish_markdown(md: str) -> str:
    """
    1) Capitalize the first letter of each heading and sentence.
    2) Ensure list items keep their dash/number and just the content is title‐cased or sentence‐cased.
    """
    lines = md.split("\n")
    out = []
    for line in lines:
        if not line.strip():
            out.append(line)
            continue

        # Headings
        if line.startswith("#"):
            hashes, rest = line.split(" ", 1)
            out.append(f"{hashes} {rest.title()}")
            continue

        # Bullets
        m = re.match(r"^([-*]\s+)(.+)", line)
        if m:
            prefix, content = m.groups()
            # Sentence‐case the content
            content = content.capitalize()
            out.append(prefix + content)
            continue

        # Numbered steps
        m = re.match(r"^(\d+\.\s+)(.+)", line)
        if m:
            prefix, content = m.groups()
            content = content.capitalize()
            out.append(prefix + content)
            continue

        # Fallback: capitalize first letter only
        out.append(line.capitalize())

    return "\n".join(out)

def add_flair(md: str) -> str:
    prompt = f"""
You’re a playful cooking assistant.  Take the following Markdown recipe and:

- Add fitting emojis to headings and list items.
- Sprinkle in a friendly, upbeat tone.
- Keep the Markdown structure intact (headings, bullets, numbers).
- Don’t change the actual instructions or ingredients.

### Recipe Markdown:
{md}

### Fun & Emoji-rich Recipe:
"""
    out = gen_model(prompt, truncation=True)[0]["generated_text"]
    return out.strip()

example = "I have egg, rice and pork. What can I make under 60 minutes preferably Asian?"

print(polish_markdown(format_recipe(queryDB(example)[0])))
