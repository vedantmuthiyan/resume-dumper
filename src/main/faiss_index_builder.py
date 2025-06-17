import json
import numpy as np
import mysql.connector
import faiss
import pickle
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv


load_dotenv()

model = SentenceTransformer('all-MiniLM-L6-v2')

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
)
cursor = conn.cursor()

cursor.execute("SELECT id, key_skills FROM extracted_data WHERE key_skills IS NOT NULL")
rows = cursor.fetchall()

ids = []
embeddings = []

for resume_id, key_skills_json in rows:
    try:
        key_skills_list = json.loads(key_skills_json)
        text = ", ".join(key_skills_list)
        embedding = model.encode(text)
        embeddings.append(embedding)
        ids.append(resume_id)
    except Exception:
        continue

if not embeddings:
    raise ValueError("No embeddings created. Check if key_skills data is valid.")

dimension = len(embeddings[0])
index = faiss.IndexFlatL2(dimension)
index.add(np.array(embeddings).astype('float32'))

with open("faiss_index.pkl", "wb") as f:
    pickle.dump((index, ids), f)

cursor.close()
conn.close()
print("FAISS index built and saved.")
