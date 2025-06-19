from langchain_google_genai import GoogleGenerativeAI
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.prompts import ChatPromptTemplate
from flask import Flask, request, jsonify
from flask_cors import CORS  # For handling CORS issues
import json
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

llm = GoogleGenerativeAI(model="gemini-2.0-flash")

template_1 = '''
Based on the table schema below, write a SQL query that would answer the user's question.
Do NOT include any markdown formatting, code blocks, or backticks in your response. Return ONLY the raw SQL query.
{schema}
Question: {question}
SQL Query:
'''
prompt_1 = ChatPromptTemplate.from_template(template_1)

template_2 = '''
Based on the table schema below, write a SQL query that would answer the user's question.
Do NOT include any markdown formatting, code blocks, or backticks in your response. Return ONLY the raw SQL query.
{schema}
Question: {question}
SQL Query:{query}
SQL Response:{response}
'''
prompt_2 = ChatPromptTemplate.from_template(template_2)

def get_schema(_):
    return db.get_table_info()

def run_query(query):
    # Clean the query by removing markdown formatting
    cleaned_query = query
    # Remove markdown code block syntax
    if "```" in cleaned_query:
        # Extract just the SQL between markdown tags if present
        import re
        sql_match = re.search(r'```(?:sql)?\s*([\s\S]*?)\s*```', cleaned_query)
        if sql_match:
            cleaned_query = sql_match.group(1)
        else:
            cleaned_query = cleaned_query.replace("```sql", "").replace("```", "")
    return db.run(cleaned_query)

db_uri = 'mysql+mysqlconnector://root:root@localhost:3306/ipl'
db = SQLDatabase.from_uri(db_uri)

# Initialize the chains
sql_chain = (
    RunnablePassthrough.assign(schema=get_schema)
    | prompt_1
    | llm.bind(stop=["\nSQLResult:"]) 
    | StrOutputParser()
)

full_chain = (
    RunnablePassthrough.assign(query=sql_chain).assign(schema=get_schema, response=lambda var: run_query(var['query']))
    | prompt_2
    | llm
)

# API endpoint to process questions
@app.route('/api/query', methods=['POST'])
def process_query():
    try:
        data = request.json
        user_question = data.get('question')
        
        if not user_question:
            return jsonify({'error': 'No question provided'}), 400
        
        # Generate SQL query
        query_result = sql_chain.invoke({'question': user_question})
        
        # Execute the query
        sql_response = run_query(query_result)
        
        # Get the final answer
        result = full_chain.invoke({'question': user_question})
        final_answer = result.text if hasattr(result, 'text') else result.content if hasattr(result, 'content') else str(result)
        
        # Return all relevant information
        return jsonify({
            'question': user_question,
            'sql_query': query_result,
            'sql_response': json.loads(json.dumps(sql_response, default=str)),  # Handle non-serializable objects
            'final_answer': final_answer
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# For testing in development
@app.route('/', methods=['GET'])
def home():
    return "SQL Query API is running. Send POST requests to /api/query"

# Only run the Flask app when this file is executed directly
if __name__ == '__main__':
    app.run(debug=True, port=5000)