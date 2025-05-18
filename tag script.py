import pandas as pd
import ast

# 1) Load your recipes CSV
df = pd.read_csv("recipes.csv")

# 2) Define a helper to parse the string-list into a real Python list
def parse_tags(s):
    if pd.isna(s) or not s.strip():
        return []
    try:
        # ast.literal_eval will turn "['a','b']" into ['a','b']
        return [t.strip() for t in ast.literal_eval(s)]
    except Exception:
        # fallback: remove brackets and split on commas
        return [t.strip().strip("'\" ") for t in s.strip("[]").split(",")]

# 3) Apply it and explode
df["tag_list"] = df["tags"].apply(parse_tags)
exploded = df[["id", "tag_list"]].explode("tag_list").rename(
    columns={"id": "recipe_id", "tag_list": "tag"}
)

# 4) Drop any empty tags
exploded = exploded[exploded["tag"].astype(bool)]

# 5) Optionally lowercase tags for consistency
exploded["tag"] = exploded["tag"].str.lower()

# 6) Write to CSV
exploded.to_csv("recipe_tags.csv", index=False, columns=["recipe_id", "tag"])