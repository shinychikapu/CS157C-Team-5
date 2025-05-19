# CS157C Team 5 Final Project Recipe Chatbot
Instructor: Dr Mike Wu

Semester: Spring 2025

Team members: Gia Thy Le, Jeffrey Chan

## Prerequisites
- Neo4j Desktop: https://neo4j.com/download/?utm_program=na-prospecting&utm_adgroup=graph-databases-general
- Node.js: https://nodejs.org/en/download
- Python (make sure you use Python 3.12 to avoid conflicts): https://www.python.org/downloads/

## Environment Setup
From the root folder run
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
## Neo4J Database Setup
Download RAW_recipes.csv from Kaggle into the root folder: https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions/data?select=RAW_recipes.csv

Run
```
python working_script.py
python tag_script.py
```
It will output recipe_ingredients.csv, recipes.csv, ingredients.csv, recipe_tags.csv. Go to Neo4J data importer tool and enter your session credentials. Upload the four outputed csv files. Create the following nodes and relationships

**Recipe Node**

![image](https://github.com/user-attachments/assets/6095ea57-bcd8-4760-9a6d-e2b34f02219f)

**Ingredient Node**

![image](https://github.com/user-attachments/assets/8a3b22c5-9c36-460a-9424-4b779069b255)

**Tag Node**

![image](https://github.com/user-attachments/assets/3fbbe58c-9f58-44dd-8f10-40acbd8e9ad6)

**HAS_INGREDIENT Relationship**

![image](https://github.com/user-attachments/assets/b558a03f-58d4-412a-b9d8-9b11075a1a69)


**HAS_TAG Relationship**

![image](https://github.com/user-attachments/assets/599fc055-e07c-4f04-be93-aaec9cf0bcdf)

## Frontend Repository
From the root folder
```
cd recipe-chatbot
```
Install dependencies
```
npm install
```
Run development server
```
npm run dev
```
Now go run the backend server
## Backend Repository
From the root folder, open another terminal separated from your front end terminal
```
cd backend
```
Run the fastapi server
```
uvicorn backend_fastapi:app  --port 4000
```
Now open ```http://localhost:5173/login``` in your browser and make a new account and ask the bot questions XD

