from langchain_google_genai import GoogleGenerativeAI
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.prompts import ChatPromptTemplate
from flask import Flask, request, jsonify
from flask_cors import CORS  # For handling CORS issues
from flask import send_file
import json
import re
load_dotenv()
# venv\Scripts\activate
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

llm = GoogleGenerativeAI(model="gemini-2.0-flash")

template_1 = '''
Based on the table schema below, write a SQL query according to MYSQL server that would answer the user's question.
you are using MYSQL server so use function of it appropriately

{schema}
Question: {question}
SQL Query:
'''
prompt_1 = ChatPromptTemplate.from_template(template_1)

template_2 = '''
Based on the table schema below, write a SQL query according to MYSQL server that would answer the user's question.
you are using MYSQL server so use function of it appropriately , if you have error in sql query so answer it simply like That's an interesting question! Unfortunately, I don't have data on that like wisw random answwer

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
    
    # Check if the query looks like a valid SQL query
    if not any(keyword in cleaned_query.lower() for keyword in ['select', 'insert', 'update', 'delete', 'create', 'alter', 'drop']):
        return "No valid SQL query could be generated for this question."
    
    return db.run(cleaned_query)

db_uri = 'mysql+mysqlconnector://root:root@localhost:3306/officemgt'
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

template_3 = '''
Based on below SQL response generate natural language anser for user for the this {question} , If you do ot have SQL query simply answer that That's an interesting question! Unfortunately, I don't have data on that like wisw random answwer
SQL Response:{response}
'''
prompt_3 = ChatPromptTemplate.from_template(template_3)

last_chain = (
    RunnablePassthrough.assign(query=sql_chain)
    .assign(schema=get_schema)
    .assign(response=lambda var: run_query(var['query']))
    | prompt_3
    | llm
)


# def clean_employee_details(text):
#     cleaned = {}
#     # Remove introductory/closing lines and split bullet points
#     lines = [line.strip() for line in text.split('\n') if line.strip() 
#             and not line.startswith('Here are') 
#             and not line.startswith('Additional details')]
    
#     for line in lines:
#         if line.startswith('*'):
#             # Remove bullet point and markdown formatting
#             clean_line = line[1:].replace('**', '').strip()
#             if ': ' in clean_line:
#                 key, value = clean_line.split(': ', 1)
#                 # Remove parenthetical numbers from values
#                 if '(' in value and ')' in value:
#                     value = value.split('(')[0].strip()
#                 cleaned[key.strip()] = value.strip()
#     return cleaned

def clean_employee_details(text):
    # Remove introductory/closing lines and special characters
    cleaned_lines = []
    for line in text.split('\n'):
        line = line.strip()
        
            # Remove bullets and bold markers
        cleaned_line = line.replace('*', '').replace('**', '')
        cleaned_lines.append(cleaned_line)
    
    # Join with single spaces instead of newlines
    return ' '.join(cleaned_lines)
# query_result = last_chain.invoke({'question': 'give me all details of Maulik'})
# print(query_result)
# print(clean_employee_details(query_result))
# print(full_chain.invoke({'question': 'What is birthdate of shlok'}))
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
        result = last_chain.invoke({'question': user_question})
        # final_answer = result.text if hasattr(result, 'text') else result.content if hasattr(result, 'content') else str(result)
        
        # Return all relevant information
        return jsonify({
            # 'final_answer': final_answer,
            'final_answer': clean_employee_details(result),
            'question': user_question
            # 'sql_query': query_result,
            # 'sql_response': json.loads(json.dumps(sql_response, default=str)),  # Handle non-serializable objects
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# For testing in development
@app.route('/', methods=['GET'])
def home():
    return "SQL Query API is running. Send POST requests to /api/query"

# Only run the Flask app when this file is executed directly

@app.route('/api/query/pdf')
def return_files_tut():
	try:
		return send_file('documents\\officemgt_live_bk_2025-06-20.sql')
	except Exception as e:
		return str(e)
if __name__ == '__main__':
    app.run(debug=True, port=5000)


