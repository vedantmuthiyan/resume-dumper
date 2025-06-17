import pickle
import mysql.connector
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import json
from dotenv import load_dotenv
import os

load_dotenv()

model = SentenceTransformer('all-MiniLM-L6-v2')

def get_resume_metadata(ids):
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )
    cursor = conn.cursor()

    format_strings = ','.join(['%s'] * len(ids))
    cursor.execute(f"SELECT id, name, email, key_skills FROM extracted_data WHERE id IN ({format_strings})", tuple(ids))
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    metadata = {}
    for row in results:
        resume_id, name, email, key_skills_json = row
        try:
            skills = json.loads(key_skills_json)
        except:
            skills = []
        metadata[resume_id] = {"name": name, "email": email, "skills": skills}
    return metadata

with open("faiss_index.pkl", "rb") as f:
    index, id_list = pickle.load(f)

query = input("Enter skills or requirements (comma-separated): ").strip()
if not query:
    print(" No input provided.")
    exit()

query_embedding = model.encode(query)
query_embedding = np.array([query_embedding]).astype('float32')

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="vedant123",
    database="company"
)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM employee_resumes")
total_resumes = cursor.fetchone()[0]

k = total_resumes

cursor.close()
conn.close()

D, I = index.search(query_embedding, k)
matched_ids = [id_list[i] for i in I[0]]

metadata = get_resume_metadata(matched_ids)

print("\n Close Matches Found:\n")
for idx in matched_ids:
    person = metadata.get(idx)
    if person:
        name = person["name"]
        email = person["email"]
        skills = person["skills"]

        skill_embeddings = model.encode(skills)
        sim_scores = cosine_similarity([query_embedding[0]], skill_embeddings)[0]
        top_idx = int(np.argmax(sim_scores))
        matched_skill = skills[top_idx] if skills else "N/A"
        similarity_percent = sim_scores[top_idx] * 100

        if similarity_percent > 50:
            print(f"ID: {idx}, Name: {name}, Email: {email}")
            print(f"Closest Skill Match: \"{matched_skill}\" ({similarity_percent:.2f}% similarity)\n")
