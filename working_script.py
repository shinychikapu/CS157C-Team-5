import pandas as pd
import ast

df = pd.read_csv("RAW_recipes.csv")

df = df.apply(lambda col: col.str.replace(r'\s+', ' ', regex=True).str.strip() if col.dtype == "object" else col)

def parse_list(s):
    if pd.isna(s) or not s.strip():
        return []
    try:
        return ast.literal_eval(s)
    except Exception:
        return []

df["ingredients_list"] = df["ingredients"].apply(parse_list)

recipes = (
    df.drop(columns=["ingredients", "ingredients_list"])
)

recipes.to_csv("recipes.csv", index=False)

rel = (
    df[["id", "ingredients_list"]]
        .explode("ingredients_list")
        .drop_duplicates()
        .rename(columns={"id": "recipe_id", "ingredients_list": "name"})
        .reset_index(drop=True)
)

ingredients = rel[["name"]].drop_duplicates().reset_index(drop=True)
ingredients["ingredient_id"] = ingredients.index

ingredients.to_csv("ingredients.csv", index=False)

recipe_ingredients = rel.merge(ingredients, on="name", how="left")[["recipe_id", "ingredient_id"]]

recipe_ingredients.to_csv("recipe_ingredients.csv", index=False)