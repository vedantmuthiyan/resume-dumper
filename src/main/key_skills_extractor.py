import mysql.connector
import json
import openai
import time
import os
from dotenv import load_dotenv
import re

load_dotenv()

openai.api_key = os.getenv("GROQ_API_KEY")
openai.api_base = "https://api.groq.com/openai/v1"

def extract_key_skills():
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )
    cursor = conn.cursor()

    cursor.execute("SHOW COLUMNS FROM extracted_data LIKE 'key_skills'")
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE extracted_data ADD COLUMN key_skills JSON")
        conn.commit()

    cursor.execute("""
                   SELECT id, skills FROM extracted_data
                   WHERE key_skills IS NULL OR JSON_LENGTH(key_skills) = 0
                   """)
    rows = cursor.fetchall()

    for resume_id, skills in rows:
        if not skills:
            print(f"Skipping ID {resume_id} - empty skills.")
            continue

        print(f"\nProcessing ID {resume_id}...\nSkills Input:\n{skills}\n")

        try:
            response = openai.ChatCompletion.create(
                model="llama-3.3-70b-versatile",
                temperature=0.4,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a resume parsing assistant.\n"
                            "You are given a list of general and detailed skills from a resume.\n"
                            "Your task is to extract only the most job-relevant individual skills.\n"
                            "Respond ONLY with a clean, uncategorized, flat JSON array of skill strings.\n\n"
                            "IMPORTANT:\n"
                            "- Do NOT group skills (e.g. don't say 'MS Office (Word, Excel)')\n"
                            "- Do NOT use categories like 'Programming Languages: ...'\n"
                            "- Just list individual skills like: \"Python\", \"Java\", \"Excel\"\n\n"
                            "Examples:\n"
                            "Input: [\"Programming Languages: C, C++, Python\", \"Soft Skills: Teamwork, Problem Solving\"]\n"
                            "Output: [\"C\", \"C++\", \"Python\", \"Teamwork\", \"Problem Solving\"]\n\n"
                            "Input: [\"MS Office (Word, Excel, PowerPoint)\", \"Data Analysis\"]\n"
                            "Output: [\"Word\", \"Excel\", \"PowerPoint\", \"Data Analysis\"]\n"
                        )

                    },
                    {
                        "role": "user",
                        "content": skills
                    }
                ]
            )

            content = response.choices[0].message.content.strip()
            print(f"Raw LLM Output:\n{content}\n")

            match = re.search(r'\[.*?\]', content, re.DOTALL)
            if match:
                key_skills = json.loads(match.group())
            else:
                print(f" No valid JSON array found for ID {resume_id}.\n")
                continue

            if isinstance(key_skills, list) and len(key_skills) > 0:
                cursor.execute(
                    "UPDATE extracted_data SET key_skills = %s WHERE id = %s",
                    (json.dumps(key_skills), resume_id)
                )
                conn.commit()
                print(f" Saved key_skills for ID {resume_id}: {key_skills}\n")
            else:
                print(f" Skipped empty or invalid key_skills for ID {resume_id}\n")

        except openai.error.RateLimitError:
            print(" Rate limited. Sleeping for 10 seconds...\n")
            time.sleep(10)
        except Exception as e:
            print(f" Error for ID {resume_id}: {e}\n")

    cursor.close()
    conn.close()


max_attempts = 5
for attempt in range(1, max_attempts + 1):
    print(f"\n Attempt {attempt}: Extracting missing or empty key_skills...")
    extract_key_skills()

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="vedant123",
        database="company"
    )
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT COUNT(*) FROM extracted_data
                   WHERE key_skills IS NULL OR JSON_LENGTH(key_skills) = 0
                   """)
    missing_count = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    if missing_count == 0:
        print(" All key_skills populated successfully.")
        break
    else:
        print(f" Still {missing_count} entries missing. Retrying in 20 seconds...\n")
        time.sleep(20)

if missing_count > 0:
    print(" Max attempts reached. Some key_skills are still missing or empty.")
