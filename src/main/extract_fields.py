import mysql.connector
import json
import openai
import re
import time

openai.api_key = "YOUR_API_KEY"
openai.api_base = "https://api.groq.com/openai/v1"

def extract_json_block(text):
    match = re.search(r"```(?:json)?\s*({.*?})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    match = re.search(r"({.*})", text, re.DOTALL)
    if match:
        return match.group(1)
    return None

def process_missing_resumes():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="vedant123",
        database="company"
    )
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS extracted_data (
                                                                    id INT PRIMARY KEY,
                                                                    name VARCHAR(255),
        email VARCHAR(255),
        education JSON,
        skills JSON,
        experience JSON,
        professionalDetails JSON
        )""")
    conn.commit()

    cursor.execute("SELECT id, content FROM employee_resumes")
    resumes = cursor.fetchall()

    for resume_id, resume_text in resumes:
        cursor.execute("SELECT skills FROM extracted_data WHERE id = %s", (resume_id,))
        existing = cursor.fetchone()
        if existing:
            try:
                skills_data = json.loads(existing[0]) if existing[0] else None
                if skills_data:
                    continue
            except json.JSONDecodeError:
                pass

        try:
            response = openai.ChatCompletion.create(
                model="deepseek-r1-distill-llama-70b",
                temperature=0.4,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert resume parser. Extract the following fields from the resume: "
                            "name, email, education (list), skills (list), experience (list), and professionalDetails (list). "
                            "Always respond with valid JSON only, no explanation. Here is an example format:\n\n"
                            "```\n"
                            "{\n"
                            "  \"name\": \"Jane Doe\",\n"
                            "  \"email\": \"jane.doe@example.com\",\n"
                            "  \"education\": [\"B.Tech in Computer Science, IIT Delhi\"],\n"
                            "  \"skills\": [\"Python\", \"Machine Learning\", \"SQL\"],\n"
                            "  \"experience\": [\"Software Engineer at Infosys (2020-2022)\"],\n"
                            "  \"professionalDetails\": [\"Worked on NLP pipelines\", \"Contributed to AI models\"]\n"
                            "}\n"
                            "```\n"
                            "Now extract the same from the following resume:"
                        )
                    },
                    {
                        "role": "user",
                        "content": resume_text
                    }
                ]
            )

            content = response.choices[0].message.content
            json_str = extract_json_block(content)
            if not json_str:
                continue

            data = json.loads(json_str)
            if not data.get("skills"):
                continue

            cursor.execute("""
                           INSERT INTO extracted_data (id, name, email, education, skills, experience, professionalDetails)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)
                               ON DUPLICATE KEY UPDATE
                                                    name=VALUES(name),
                                                    email=VALUES(email),
                                                    education=VALUES(education),
                                                    skills=VALUES(skills),
                                                    experience=VALUES(experience),
                                                    professionalDetails=VALUES(professionalDetails)
                           """, (
                               resume_id,
                               data.get("name"),
                               data.get("email"),
                               json.dumps(data.get("education")),
                               json.dumps(data.get("skills")),
                               json.dumps(data.get("experience")),
                               json.dumps(data.get("professionalDetails"))
                           ))
            conn.commit()

        except openai.error.RateLimitError:
            print(f"Rate limited on resume {resume_id}, retrying after 15s...")
            time.sleep(15)
            continue
        except Exception as e:
            print(f"Error processing resume ID {resume_id}: {e}")
            continue

    cursor.execute("SELECT COUNT(*) FROM employee_resumes")
    total_resumes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM extracted_data WHERE skills IS NOT NULL")
    processed_resumes = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return total_resumes == processed_resumes

max_attempts = 3
attempt = 1
while attempt <= max_attempts:
    print(f"\nAttempt {attempt}: Processing missing or null-skill resumes...")
    success = process_missing_resumes()
    if success:
        print("All resumes processed with non-null skills.")
        break
    else:
        print("Still missing some skills. Retrying after 20s...")
        time.sleep(20)
        attempt += 1

if attempt > max_attempts:
    print("Max attempts reached. Some resumes may still have null skills.")
