from neo4j import GraphDatabase
import json
import re
from contextlib import asynccontextmanager
import os

def extract_ingredients(text, gen_model) -> list:
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

def extract_tags(text, tag_model, threshold=0.8):
    out = tag_model(text, POSSIBLE_TAGS)
    tags = [
        label for label, score in zip(out["labels"], out["scores"])
        if score >= threshold
    ]

    time_tags = []
    for t in tags:
        m = re.match(r"(\d+)-minutes-or-less", t)
        if m:
            time_tags.append((int(m.group(1)), t))
    
    if time_tags:
        biggesst, best_tag = max(time_tags, key=lambda x: x[0])
        tags = [t for t in tags if not re.match(r"\d+-minutes-or-less", t)]
        tags.append(best_tag)

    return tags

def extractor(text,gen_model, tag_model):
    ingredients = extract_ingredients(text, gen_model)
    tags = extract_tags(text, tag_model)
    return{
        "ingredients": ingredients,
        "tags" : tags
    }

def queryDB(text, driver, gen_model, tag_model):
    session = driver.session()
    try:
        # 1) Extract ingredients & tags
        extraction  = extractor(text, gen_model, tag_model)
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
  .id,
  .name,
  .description,
  ingredients:    allIng,
  steps:          r.steps
} AS recipe
ORDER BY ingredientExtras ASC
LIMIT 10;
"""
        else:
            print(1)
            cypher = """
WITH $ingredients AS wantIng, $tags AS wantTags

// Find Recipe with required ingredients
MATCH (r:Recipe)-[:HAS_INGREDIENT]->(ing:Ingredient)
WITH r, collect(DISTINCT toLower(ing.name)) AS allIng, wantIng, wantTags
WHERE all(req IN wantIng 
          WHERE any(act IN allIng WHERE act STARTS WITH req))

// Get all tags for the recipe
OPTIONAL MATCH (r)-[:HAS_TAG]->(t:Tag)
WITH 
  r, 
  allIng, 
  collect(DISTINCT toLower(t.tag)) AS recipeTags,
  wantTags,
  size(allIng) - size(wantIng) AS ingredientExtras

// Compute how many tags match
WITH 
  r, 
  allIng, 
  recipeTags,
  ingredientExtras,
  [tag IN wantTags WHERE tag IN recipeTags] AS matchedTags

// Return recipe info + match score
RETURN r {
  .id,
  .name,
  .description,
  ingredients: allIng,
  steps: r.steps,
  matchedTagCount: size(matchedTags)
} AS recipe
ORDER BY size(matchedTags) DESC, ingredientExtras ASC
LIMIT 10
"""
        params = {"ingredients": ingredients, "tags": tags}
        print(tags, "\n", cypher, "\n", params)
        result  = session.run(cypher, params)
        recipes = [record["recipe"] for record in result]
        print("returning queries")
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


def format_recipe(recipe: dict) -> str:
    name        = recipe.get("name", "")
    description = recipe.get("description", "")
    ingredients = recipe.get("ingredients", [])
    steps       = parse_steps(recipe.get("steps", []))
    
    lines = []
    # Title
    lines.append(f"### 🍽️ {name.title()}\n")

    # Description
    if description:
        lines.append(f"#### ✒️ Description: \n{description}\n")

    # Ingredients
    lines.append("#### 📋 Ingredients:")
    for ing in ingredients:
        lines.append(f"- {ing}")
    lines.append("")  # blank line

    # Steps
    lines.append("#### 🍳 Steps:")
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
        m = re.match(r"^([-]\s+)(.+)", line)
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
    print("polished")
    return "\n".join(out)

#example = "I have egg, rice and pork. What can I make under 60 minutes preferably Asian?"

#print(polish_markdown(format_recipe(queryDB(example)[0])))