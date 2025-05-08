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

model_name = "google/flan-t5-base"
tok   = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)

if device >= 0:
    model = model.to(f"cuda:{device}")

# Tag Classification model
tag_model = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli",
    device=device,
    # enable multi‐label classification
    multi_label=True,
)

# LLM for ingredients extraction
gen_model = pipeline(
    "text2text-generation",
    model=model,
    tokenizer=tok,
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
    print(result)
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
