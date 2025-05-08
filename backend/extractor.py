from transformers import AutoModelForSeq2SeqLM, AutoTokenizer,pipeline
import torch
from neo4j import GraphDatabase
import json
import re

device = 0 if torch.cuda.is_available() else -1

model_name = "google/flan-t5-base"
tok   = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)


if device >= 0:
    model = model.to(f"cuda:{device}")

# Tag Classification model
tag_model = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli",
    device=device,        
)

# LLM for ingredients extraction
gen_model = pipeline(
    "text2text-generation",
    model=model,
    tokenizer=tok,
    device=device,
)

def extract_ingredients(text: str) -> list:
    # 1) Build a few-shot prompt with clear “Input→Output” examples
    prompt = f"""
You are a kitchen assistant.  Extract only the ingredient names from the user’s request.
Respond with a comma-separated list, nothing else.

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
    return [i.strip() for i in csv.split(",") if i.strip()]




# Tags extraction
POSSIBLE_TAGS = [
 '60-minutes-or-less',
 '30-minutes-or-less',
 '15-minutes-or-less',

 'vegetarian',
 'vegan',
 'gluten-free',
 'diabetic',
 'dairy-free',
 'egg-free',
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
 'indian',
 'french',
 'chinese',
 'european',
 'south-american',
 'middle-eastern',
 'thai',
 'japanese',
 'greek'

 'christmas',
 'thanksgiving',
 'easter',
 'halloween',
 'birthday'
]

def extract_tags(text, threshold=0.5):
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
example = "I have rice, beef and egg. What can I make under 30 minutes?"

# Example
print(extractor(example))
