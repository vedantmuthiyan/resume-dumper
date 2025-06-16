
# Resume Parser & Similarity Search System

This project is a hybrid Java-Python application designed to:

1. Extract full resume text from PDF files using Java.
2. Use an LLM to extract structured fields from resumes and populate a MySQL database.
3. Generate key job-relevant skills from the resume using an LLM.
4. Build a FAISS vector index for similarity search on key skills.
5. Query resumes based on user-specified skills and return top matches with cosine similarity.

---

## 🛠️ Technologies Used

- Java (Maven)
- Python 3.11+
- MySQL
- FAISS (Facebook AI Similarity Search)
- SentenceTransformers
- OpenAI/Groq API for LLM-based skill extraction

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/resume-dumper.git
cd resume-dumper
```

### 2. Install Python Dependencies

```bash
pip install mysql-connector-python sentence-transformers faiss-cpu openai
```

> Ensure Python 3.11+ is installed and available in your `PATH`.

### 3. Set up MySQL Database

Create a database called `company` and ensure the following tables exist:

- `employee_resumes(id, content)`
- `extracted_data(id, name, email, ..., skills, key_skills)`

Make sure the `key_skills` column is of type `JSON`.

---

## ▶️ Running the Project

### Step 1: Run Resume PDF Parser (Java)

```bash
mvn exec:java
```

This extracts full resume content from PDF files and stores it in `employee_resumes`.

### Step 2: Run Field Extraction (Python)

```bash
python src/main/extract_fields.py
```

This uses an LLM to extract fields like name, email, education, experience, and skills into `extracted_data`.

### Step 3: Generate Key Skills Using LLM

```bash
python src/main/key_skills_extractor.py
```

This identifies the most job-relevant skills and populates the `key_skills` column in `extracted_data`.

### Step 4: Build FAISS Index

```bash
python src/main/faiss_index_builder.py
```

This creates a FAISS index using SentenceTransformer embeddings from the `key_skills`.

### Step 5: Run Similarity Search

```bash
python src/main/query_faiss.py
```

This matches user-provided skills against resume key skills using cosine similarity.

---

## 📌 Notes

- Set your Groq API key in `key_skills_extractor.py`.
- FAISS uses cosine similarity on SentenceTransformer embeddings.
- Adjust similarity threshold (`FAISS_THRESHOLD`) in `query_faiss.py` to control how strict or flexible matches are.
- Key skills should be flat (e.g., `"Python", "Excel"`) — avoid nested or categorized formats like `"Programming: C, C++"`.

---
