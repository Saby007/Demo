from flask import Flask, request, jsonify
from openai import AzureOpenAI
import pyodbc
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2023-12-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# Function to generate SQL from natural language
def get_sql_from_natural_query(user_query):
    prompt = f"""You are a helpful assistant that converts English to SQL.
The table name is `Reports` with columns: `Report_ID` (GUID) and `Report_Name` (text).

English: {user_query}
SQL:"""

    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    #return response.choices[0].message.content.strip()
    import re

    raw_sql = response.choices[0].message.content.strip()

    # Remove markdown code block if present (```sql ... ```)
    cleaned_sql = re.sub(r"^```sql\s*|```$", "", raw_sql.strip(), flags=re.IGNORECASE | re.MULTILINE).strip()

    return cleaned_sql

# Function to execute SQL on Azure SQL DB
def run_sql_query(query):
    server = os.getenv("AZURE_SQL_SERVER")
    database = os.getenv("AZURE_SQL_DB")
    username = os.getenv("AZURE_SQL_USERNAME")
    password = os.getenv("AZURE_SQL_PASSWORD")

    connection_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
    )

    try:
        with pyodbc.connect(connection_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                if cursor.description:
                    columns = [column[0] for column in cursor.description]
                    rows = cursor.fetchall()
                    return [dict(zip(columns, row)) for row in rows]
                else:
                    conn.commit()
                    return {"status": "success", "message": "Query executed."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Flask route
@app.route("/query", methods=["POST"])
def query():
    user_query = request.json.get("query")
    if not user_query:
        return jsonify({"error": "Missing 'query' in request"}), 400

    sql_query = get_sql_from_natural_query(user_query)
    result = run_sql_query(sql_query)

    return jsonify({
        "user_query": user_query,
        "sql_generated": sql_query,
        "result": result
    })

if __name__ == "__main__":
    app.run(debug=True)
