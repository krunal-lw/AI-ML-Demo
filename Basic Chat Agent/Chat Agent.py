from langchain_google_genai import GoogleGenerativeAI, ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.prompts import ChatPromptTemplate
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS 
from langchain.tools import tool
from fpdf import FPDF
from langchain import hub
from langchain.agents import create_react_agent, AgentExecutor
from langchain.memory import ConversationSummaryMemory 
from langchain.schema import HumanMessage, AIMessage
import mysql.connector
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from decimal import Decimal
from datetime import date, datetime
import os
import uuid
from typing import Dict, List
import re
from langchain.memory import ConversationSummaryMemory
import logging
from functools import lru_cache


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
app = Flask(__name__)
CORS(app)
request_context = {}
 
chat_sessions: Dict[str, List[Dict]] = {}
AUTHORIZED_EMAILS = ['kaushal.bhojani@logicalwings.com', 'pratik@logicalwings.com']
DB_URI = 'mysql+mysqlconnector://root:root@localhost:3306/officemgt'
db = SQLDatabase.from_uri(DB_URI)
DB_CONFIG = {
    'host': "localhost",
    'user': "root", 
    'password': "root",
    'database': "officemgt"
}
# llama_repo_id = "meta-llama/Llama-3.1-8B-Instruct"
# llmh = HuggingFaceEndpoint(
#     model=llama_repo_id, task="conversational"
# )
 
# llm = ChatHuggingFace(llm=llmh)

session_memories: Dict[str, ConversationSummaryMemory] = {}

@lru_cache(maxsize=1)
def get_llm():
    return GoogleGenerativeAI(model="gemini-2.5-flash")

@lru_cache(maxsize=1)
def get_chat_llm():
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash")

@lru_cache(maxsize=1)
def get_database():
    return SQLDatabase.from_uri(DB_URI)

# Initialize database connection
db = get_database()

def get_or_create_memory(session_id: str) -> ConversationSummaryMemory:
    """Get or create memory for a session"""
    if session_id not in session_memories:
        session_memories[session_id] = ConversationSummaryMemory(
            llm=get_llm(),
            memory_key="chat_history",
            return_messages=True
        )
    return session_memories[session_id]

def add_to_memory(session_id: str, user_message: str, ai_response: str):
    """Add conversation to memory and force summary generation"""
    memory = get_or_create_memory(session_id)
    memory.chat_memory.add_user_message(user_message)
    memory.chat_memory.add_ai_message(ai_response)
    
    # Force summary generation after every 4 messages
    if len(memory.chat_memory.messages) >= 4:
        force_summarize_memory(session_id)

def force_summarize_memory(session_id: str):
    """Force summary generation for a session"""
    memory = get_or_create_memory(session_id)
    if memory.chat_memory.messages:
        messages = memory.chat_memory.messages
        # Force summary generation
        memory.buffer = memory.predict_new_summary(messages, memory.buffer or "")
        print(f"🔄 Generated summary for session {session_id}: {memory.buffer}")

def get_memory_summary(session_id: str) -> str:
    """Get the conversation summary for a session"""
    memory = get_or_create_memory(session_id)
                          
    # If buffer is empty but we have messages, force generate summary
    if (not memory.buffer or memory.buffer.strip() == "") and memory.chat_memory.messages:
        force_summarize_memory(session_id)
    
    return memory.buffer or "No conversation summary yet."

def get_memory_context(session_id: str) -> str:
    """Get formatted memory context for prompts including summary"""
    memory = get_or_create_memory(session_id)
    messages = memory.chat_memory.messages
    summary = get_memory_summary(session_id)
    
    if not messages:
        return "This is the start of the conversation."
    
    # Include summary in context
    context = f"Conversation Summary: {summary}\n\nRecent Messages:\n"
    
    # Get last 6 messages for recent context
    formatted = []
    for msg in messages[-6:]:
        if isinstance(msg, HumanMessage):
            formatted.append(f"Human: {msg.content}")
        elif isinstance(msg, AIMessage):
            formatted.append(f"Assistant: {msg.content}")
    
    context += "\n".join(formatted)
    return context

# Store chat sessions (keeping for compatibility)

def authorized_email(email):
    print(email)
    if email not in AUTHORIZED_EMAILS:
        print('employee')

        template_1 = '''
        You are a MySQL query generator. Follow these STRICT rules:

        CRITICAL REQUIREMENTS:
        1. Current user email: {email}
        2. Access Control Rules:
            a) Include a WHERE clause for email in EVERY query

        QUERY REQUIREMENTS:
        - Generate only valid MySQL syntax
        - Use appropriate MySQL functions
        - Never expose email addresses in query results
        - Return only the SQL query, no explanations

        Table Schema:
        {schema}

        User Question: {question}

        Generate MySQL Query:
        '''
        
    else:
        print('admin')
        template_1 = '''
    Based on the table schema below, write a SQL query according to MYSQL server that would answer the user's question.
    you are using MYSQL server so use function of it appropriately
    always use employee code in where clause for each employee

    {schema}
    Question: {question}
    SQL Query:
        '''
    prompt_1 = ChatPromptTemplate.from_template(template_1)
    return prompt_1

@lru_cache(maxsize=3)
def get_prompt_templates():
    """Cache prompt templates"""
    template_3 = '''
        Previous conversation context:
        {memory_context}
        please provide answer in user's message language
        Based on below SQL response generate natural language answer for user for this {question}. 
        If you don't have SQL query simply answer that "That's an interesting question! Unfortunately, I don't have data on that" with a helpful response.
        provide clear and short answer
        Always be conversational and friendly in your response.

        Use the conversation context to provide more personalized responses.

        SQL Response:{response}
        '''
    
    chatbot_template = '''
            please provide answer in user's message language

            You are an intelligent Office Management Assistant chatbot. You can help with:
            Instructions:
            - Be conversational, friendly, and professional
            - If user requests salary slip generation, use the salary slip tool
            - If user asks for something you can't do, politely explain and offer alternatives
            - Always maintain context from previous messages in the conversation
            - Be helpful and provide clear and short answer
            - Use the conversation history to provide more personalized and contextual responses

            Previous conversation history:
            {memory_context}

            User Message: {user_message}
            Assistant Response:
            '''
    
    return {
        'prompt_3': ChatPromptTemplate.from_template(template_3),
        'chatbot_prompt': ChatPromptTemplate.from_template(chatbot_template)
    }


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

def create_sql_chain_with_memory(session_id: str):
    """Create SQL chain with memory context"""
    prompt_1 = authorized_email(request_context.get('email', ''))
    return (
        RunnablePassthrough.assign(
            schema=get_schema,
            memory_context=lambda _: get_memory_context(session_id),
            email=lambda _: request_context.get('email', '')        
        )
        | prompt_1
        | get_llm().bind(stop=["\nSQLResult:"]) 
        | StrOutputParser()
    )

def create_full_chain_with_memory(session_id: str):
    """Create full chain with memory context"""
    templates = get_prompt_templates()
    sql_chain = create_sql_chain_with_memory(session_id)
    return (
        RunnablePassthrough.assign(
            query=sql_chain,
            memory_context=lambda _: get_memory_context(session_id)
        ).assign(
            response=lambda var: run_query(var['query'])            
        )
        | templates['prompt_3']
        | get_llm()
    )

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


def format_chat_history(messages: List[Dict]) -> str:
    """Format chat history for context (legacy support)"""
    if not messages:
        return "This is the start of the conversation."
    
    formatted = []
    for msg in messages[-5:]:  # Keep last 5 messages for context
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        formatted.append(f"{role.capitalize()}: {content}")
    
    return "\n".join(formatted)

class SalarySlipPDF(FPDF):
    def __init__(self, logo_path='image.png'):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.logo_path = logo_path
        
    def header(self):
        # Add company logo on the left side
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                # Place logo on left side - adjust dimensions as needed
                self.image(self.logo_path, 10, 10, 40, 20)  # x, y, width, height
            except:
                # If logo file not found, create a placeholder box
                self.set_font('Arial', 'B', 8)
                self.set_xy(10, 10)
                self.cell(40, 20, 'LOGO', 1, 0, 'C')
                print(f"Warning: Logo file '{self.logo_path}' not found. Using placeholder.")
        else:
            # Create a placeholder box if no logo path provided
            self.set_font('Arial', 'B', 8)
            self.set_xy(10, 10)
            self.cell(40, 20, 'LOGO', 1, 0, 'C')
        
        # Company name centered
        self.set_font('Arial', 'B', 12)
        self.set_xy(0, 15)  # Position for company name
        self.cell(0, 10, 'LOGICAL WINGS INFOWEB PVT. LTD.', 0, 1, 'C')
        self.ln(10)
        
    def create_salary_slip(self, employee_data, salary_data, month_year):
        self.add_page()
        
        # Title
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, f'SALARY SLIP - {month_year.upper()}', 0, 1, 'C')
        self.ln(10)
        
        # Employee Information Table
        self.create_employee_info_table(employee_data)
        self.ln(10)
        
        # Working Days Information
        self.create_working_days_table(salary_data['working_days'])
        self.ln(10)
        
        # Salary Details Table
        self.create_salary_table(salary_data)
        self.ln(10)
        
        # CTC Information
        self.create_ctc_info(salary_data)
        self.ln(10)
        
        # Digital Signature
        self.create_signature_section()
        
    def create_employee_info_table(self, employee_data):
        # Set font for table content
        self.set_font('Arial', '', 10)
        
        # Define column widths
        col_width = 95
        
        # Employee information rows
        info_rows = [
            ('Employee ID', employee_data['employee_id']),
            ('Employee Name', employee_data['name']),
            ('Designation', employee_data['designation']),
            ('Department', employee_data['department']),
            ('Location', employee_data['location']),
            ('Date of Joining', employee_data['joining_date']),
            ('P.F. No.', employee_data['pf_no']),
            ('UAN No.', employee_data['uan_no']),
            ('ESI No.', employee_data['esi_no']),
            ('Bank Name', employee_data['bank_name']),
            ('Bank A/C No.', employee_data['account_no'])
        ]
        
        # Create bordered table
        for label, value in info_rows:
            self.cell(col_width, 7, label, 1, 0, 'L')
            self.cell(col_width, 7, str(value), 1, 1, 'L')
    
    def create_working_days_table(self, working_days_data):
        self.set_font('Arial', '', 10)
        col_width = 95
        
        self.cell(col_width, 7, f"Actual Working Days: {working_days_data['actual']}", 1, 0, 'L')
        self.cell(col_width, 7, f"Paid Days: {working_days_data['paid']}", 1, 1, 'L')
    
    def create_salary_table(self, salary_data):
        # Table header
        self.set_font('Arial', 'B', 10)
        col_widths = [95, 47.5, 47.5]
        
        self.cell(col_widths[0],7, 'Description', 1, 0, 'C')
        self.cell(col_widths[1], 7, 'Actual Rs.', 1, 0, 'C')
        self.cell(col_widths[2], 7, 'Payable Rs.', 1, 1, 'C')
        
        # Salary components
        self.set_font('Arial', '', 10)
        components = [
            ('Basic + DA', salary_data['basic_da'], salary_data['basic_da']),
            ('HRA', salary_data['hra'], salary_data['hra']),
            ('LTA', salary_data['lta'], salary_data['lta']),
            ('Conveyance Allowance', salary_data['conveyance'], salary_data['conveyance']),
            ('Medical Allowance', salary_data['medical'], salary_data['medical']),
            ('Special Allowance', salary_data['special'], salary_data['special'])
        ]
        
        for desc, actual, payable in components:
            self.cell(col_widths[0], 7, desc, 1, 0, 'L')
            # Bold zero values
            if actual == 0:
                self.set_font('Arial', 'B', 10)
            self.cell(col_widths[1], 7, str(actual), 1, 0, 'C')
            self.cell(col_widths[2], 7, str(payable), 1, 1, 'C')
            if actual == 0:
                self.set_font('Arial', '', 10)
        
        # Gross Salary row
        self.set_font('Arial', 'B', 10)
        self.cell(col_widths[0], 7, 'Gross Salary(Total Earnings)', 1, 0, 'L')
        self.cell(col_widths[1], 7, str(salary_data['gross_salary']), 1, 0, 'C')
        self.cell(col_widths[2], 7, str(salary_data['gross_salary']), 1, 1, 'C')
        
        self.ln(5)
        
        # Deductions
        self.set_font('Arial', '', 10)
        deduction_col_width = 95
        self.cell(deduction_col_width, 7, 'Professional Tax (PT)', 1, 0, 'L')
        self.cell(deduction_col_width, 7, f"{salary_data['professional_tax']}", 1, 1, 'C')
        
        # Net Salary
        self.set_font('Arial', 'B', 10)
        self.cell(deduction_col_width, 7, 'Net Salary', 1, 0, 'L')
        self.cell(deduction_col_width, 7, f"{salary_data['net_salary']:.2f}", 1, 1, 'C')
        
        self.ln(5)
        self.set_font('Arial', '', 10)

    def create_ctc_info(self, salary_data):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 8, f"Total CTC (Monthly): Rs. {salary_data['monthly_ctc']}", 0, 1, 'L')
        self.cell(0, 8, f"Total CTC (Annually): Rs.{salary_data['annual_ctc']}", 0, 1, 'L')
    
    def create_signature_section(self):
        self.ln(10)
        self.set_font('Arial', '', 9)
        
        signature_info = [
            "Digitally Signed by: [Pratik Trivedi]",
            "Designation: [HR Executive]",
            f"Signed on: {datetime.now().strftime('%d/%m/%Y')}",
            "This document is digitally verified and authorized."
        ]
        
        for line in signature_info:
            self.cell(0, 6, line, 0, 1, 'L')
        
        self.ln(5)
        self.set_font('Arial', 'B', 8)
        self.cell(0, 6, "*** This is a computer-generated salary slip and does not require a", 0, 1, 'C')
        self.cell(0, 6, "physical signature. ***", 0, 1, 'C')

def get_db_connection():
    """Get database connection with error handling"""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise

def format_sql_result_row(result_row):  
    if isinstance(result_row, list) and result_row:
        row = result_row[0]
    elif isinstance(result_row, tuple):
        row = result_row
    else:
        return []

    cleaned_values = []
    for value in row:
        # if value is None or value == '':
        if value is None:
            cleaned_values.append(0)
        elif value == '':
            cleaned_values.append('-')

        elif isinstance(value, int):
            cleaned_values.append(value)
        elif isinstance(value, Decimal):
            cleaned_values.append(float(value))
        elif isinstance(value, date):
            cleaned_values.append(value.strftime('%Y-%m-%d'))
        else:
            cleaned_values.append(str(value))

    return cleaned_values
@tool
def generate_custom_salary_slip(emp_id):
    """
    Always try to extract employee IDs if mentioned — they will start with 'LWE' or 'ADMIN'
    Generate a salary slip with employee details and salary details.
    Args:
        emp_id (str): ID of the employee start With LWE or ADMIN
    
    Returns:
        str: Filename of the generated PDF or error message
    """
    try:
        pattern = r'\b(?:LWE|ADMIN)\d+\b'
        matches = re.findall(pattern, emp_id, re.IGNORECASE)
        
        if not matches:
            return "Invalid employee ID format. Please use format like LWE123 or ADMIN123."
        
        emp_code = matches[0]
        # conn = mysql.connector.connect(
        #     host="localhost",
        #     user="root",
        #     password="root",
        #     database="officemgt"
        # )
        # cursor = conn.cursor()
        query = '''SELECT 
                E.EmployeeCode,
                CONCAT(E.FirstName, 
                       CASE WHEN E.MiddleName IS NOT NULL AND E.MiddleName != '' 
                            THEN CONCAT(' ', E.MiddleName) ELSE '' END,
                       CASE WHEN E.LastName IS NOT NULL AND E.LastName != '' 
                            THEN CONCAT(' ', E.LastName) ELSE '' END) AS Fullname,
                COALESCE(D.Name, 'N/A') as Designation,
                COALESCE(DE.Name, 'N/A') as Department,
                COALESCE(C.Name, 'N/A') as City,
                E.DateOfJoining,
                COALESCE(E.PFno, '-') as PFno,
                COALESCE(E.ESICno, '-') as ESICno,
                COALESCE(EBA.AccountNO, '-') as AccountNO,
                COALESCE(B.Name, 'N/A') as BankName,
                COALESCE(SS.BasicSalary, 0) as BasicSalary, 
                COALESCE(SS.HRA, 0) as HRA,
                COALESCE(SS.LTA, 0) as LTA,
                COALESCE(SS.ConveyanceAllowance, 0) as ConveyanceAllowance, 
                COALESCE(SS.MedicalAllowance, 0) as MedicalAllowance,
                COALESCE(SS.SpecialAllowance, 0) as SpecialAllowance, 
                COALESCE(SS.ProfessionalTax, 0) as ProfessionalTax,
                COALESCE(E.CTCmonthlySalary, 0) as CTCmonthlySalary
            FROM employee AS E
            LEFT JOIN designation AS D ON E.DesignationID = D.ID 
            LEFT JOIN department AS DE ON E.DepartmentID = DE.ID
            LEFT JOIN city AS C ON E.CityIDlocal = C.ID
            LEFT JOIN employeebankaccountdetail AS EBA ON E.ID = EBA.EmpID
            LEFT JOIN bank AS B ON EBA.BankID = B.ID
            LEFT JOIN salaryslip AS SS ON E.ID = SS.EmpID
        WHERE E.EmployeeCode = %s
        '''
        params = [emp_code]
        requester_email = request_context.get('email', '')
        # print(requester_email)
        
        if requester_email.lower() not in ['kaushal.bhojani@logicalwings.com' , 'pratik@logicalwings.com']:
            query += 'and E.Companyemail = %s'
            params.append(requester_email)

        # print(matches)
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchall()
        
        if not result:
            return f"Access denied, You can not Generate other employee's Salary Slip 😉"

        
        
        final_ans = format_sql_result_row(result)

        custom_employee = {
            'employee_id': final_ans[0],
            'name': final_ans[1],
            'designation': final_ans[2],
            'department': final_ans[3],
            'location': final_ans[4],
            'joining_date': final_ans[5],
            'pf_no': final_ans[6],
            'uan_no': 'UAN789012',
            'esi_no': final_ans[7],
            'bank_name': final_ans[9],
            'account_no': final_ans[8]
        }
        
        custom_salary = {
            'working_days': {
                'actual': 30,
                'paid': 30
            },
            'basic_da': final_ans[10],
            'hra': final_ans[11],
            'lta': final_ans[12],
            'conveyance': final_ans[13],
            'medical': final_ans[14],
            'special': final_ans[15],
            'gross_salary': sum(float(x) for x in final_ans[10:16]),
            'professional_tax': float(final_ans[16]),
            'net_salary': sum(float(x) for x in final_ans[10:16]) - float(final_ans[16]),
            'monthly_ctc': final_ans[17],
            'annual_ctc': int(final_ans[17]) * 12
        }

        pdf = SalarySlipPDF()
        pdf.create_salary_slip(custom_employee, custom_salary,month_year= "MAY 2025")
    
        output_filename = f"salary_slip_{emp_code}.pdf"
        pdf.output(output_filename)
        print(f"Custom salary slip generated: {output_filename}")
        
        return output_filename
    
    except Exception as e:
        logger.error(f"Error generating salary slip: {str(e)}")
        return f"Error generating salary slip: {str(e)}"

tools = [generate_custom_salary_slip]

@lru_cache(maxsize=1)
def get_agent_prompt():
    return hub.pull("hwchase17/react")

def create_agent_with_memory():
    """Create agent with memory context"""
    agent = create_react_agent(get_llm(), tools, get_agent_prompt())
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

def get_session_summary(session_id: str) -> Dict:
    """Get session summary and statistics"""
    memory = get_or_create_memory(session_id)
    summary = get_memory_summary(session_id)
    
    return {
        'session_id': session_id,
        'summary': summary,
        'message_count': len(memory.chat_memory.messages),
        'has_summary': bool(summary and summary.strip())
    }

def determine_intent(message: str , session_id: str):
    """Determine user intent from message"""
    message_lower = message.lower()
    
    intent_templet ="""

                     Previous conversation context:
                        {memory_context}
                        You are an AI assistant that determines the intent behind a user's question.

                There are three possible intents:
                1. salary_slip_generation → If the question is about generating or creating salary slips.
                2. employee_from_mysql → If the question is about retrieving or interacting with employee data from a MySQL database. if question like what is my name,what is my mobile number , what is my address this all type question fall into this category
                3. general_question → If the question doesn't match the above categories and is more general.

                Classify the following user question into one of these three intents. 
                Only return the intent name (e.g., salary_slip_generation, employee_from_mysql, general_question) as output.

                User Question: "{user_question}"

                    Intent:
                    """
    intent = ChatPromptTemplate.from_template(intent_templet)
    result = get_llm().invoke(intent.format(memory_context=get_memory_context(session_id) , user_question=message_lower))
    response_content = result.content if hasattr(result, 'content') else str(result)
    return response_content.strip()

def _handle_salary_slip_generation(session_id: str, user_message: str) -> Dict:
    """Handle salary slip generation"""
    # memory_context = get_memory_context(session_id)
    agent_executor = create_agent_with_memory()
    
    # Previous conversation context:
    # {memory_context}
    enhanced_input = f"""
    
    Current request: {user_message}
    """
    
    result = agent_executor.invoke({"input": enhanced_input})
    response_text = result.get('output', 'I encountered an issue generating the salary slip.')
    
    # Check if PDF was generated
    filename_match = re.search(r'salary_slip[\w_]+\.pdf', response_text)
    
    response = {
        'message': response_text,
        'type': 'salary_slip',
        'file_generated': bool(filename_match),
        'filename': filename_match.group(0) if filename_match else None,
        'download_url': f'/api/download/{filename_match.group(0)}' if filename_match else None
    }
    
    add_to_memory(session_id, user_message, response_text)
    return response

def _handle_employee_info(session_id: str, user_message: str) -> Dict:
    """Handle employee information queries"""
    last_chain = create_full_chain_with_memory(session_id)
    result = last_chain.invoke({'question': user_message})
    cleaned_result = clean_employee_details(result)
    sql = create_sql_chain_with_memory(session_id).invoke({'question': user_message})
    
    response = {
        'sql': sql,
        'message': cleaned_result,
        'type': 'employee_info',
        'file_generated': False
    }
    
    add_to_memory(session_id, user_message, cleaned_result)
    return response

def _handle_general_conversation(session_id: str, user_message: str) -> Dict:
    """Handle general conversation"""
    templates = get_prompt_templates()
    memory_context = get_memory_context(session_id)
    
    general_response = get_chat_llm().invoke(
        templates['chatbot_prompt'].format(
            memory_context=memory_context,
            user_message=user_message
        )
    )
    
    response_content = general_response.content if hasattr(general_response, 'content') else str(general_response)
    
    response = {
        'message': response_content,
        'type': 'general',
        'file_generated': False
    }
    
    add_to_memory(session_id, user_message, response_content)
    return response

def _handle_error(session_id: str, user_message: str, error_msg: str) -> Dict:
    """Handle errors"""
    error_message = f"I'm sorry, I encountered an error: {error_msg}. Please try again or rephrase your question."
    error_response = {
        'message': error_message,
        'type': 'error',
        'file_generated': False
    }
    
    add_to_memory(session_id, user_message, error_message)
    
    chat_sessions[session_id].append({
        'role': 'assistant',
        'content': error_response['message'],
        'timestamp': datetime.now().isoformat(),
        'type': 'error'
    })
    
    return error_response

def process_user_message(session_id: str, user_message: str) -> Dict:
    """Process user message and return appropriate response"""
    
    # Initialize session if not exists (for compatibility)
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
    
    # Add user message to legacy session (for compatibility)
    chat_sessions[session_id].append({
        'role': 'user',
        'content': user_message,
        'timestamp': datetime.now().isoformat()
    })
    
    # session_info = get_session_summary(session_id)
    # print(f"📋 Session Info: {session_info}")
    
    # Determine intent
    intent = determine_intent(user_message, session_id)
    
    try:
        if intent == 'salary_slip_generation':
            response = _handle_salary_slip_generation(session_id, user_message)
        elif intent == 'employee_from_mysql':
            response = _handle_employee_info(session_id, user_message)
        else:
            response = _handle_general_conversation(session_id, user_message)
        
        # Add assistant response to legacy session (for compatibility)
        chat_sessions[session_id].append({
            'role': 'assistant',
            'content': response['message'],
            'timestamp': datetime.now().isoformat(),
            'type': response['type']
        })
        
        # Print final session summary after processing
        final_session_info = get_session_summary(session_id)
        print(f"📋 Final Session Info: {final_session_info}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return _handle_error(session_id, user_message, str(e))
@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chatbot endpoint"""
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', str(uuid.uuid4()))
        email = data.get('email')
        request_context['email'] = email
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        response = process_user_message(session_id, user_message)
        response['session_id'] = session_id
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/history/<session_id>', methods=['GET'])
def get_chat_history(session_id):
    """Get chat history for a session"""
    try:
        # Get from memory
        memory = get_or_create_memory(session_id)
        memory_messages = []
        
        for msg in memory.chat_memory.messages:
            if isinstance(msg, HumanMessage):
                memory_messages.append({
                    'role': 'user',
                    'content': msg.content,
                    'timestamp': datetime.now().isoformat()
                })
            elif isinstance(msg, AIMessage):
                memory_messages.append({
                    'role': 'assistant',
                    'content': msg.content,
                    'timestamp': datetime.now().isoformat()
                })
        
        # Fallback to legacy session for compatibility
        legacy_history = chat_sessions.get(session_id, [])
        
        return jsonify({
            'memory_history': memory_messages,
            'legacy_history': legacy_history,
            'session_id': session_id
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/clear/<session_id>', methods=['DELETE'])
def clear_chat_history(session_id):
    """Clear chat history for a session"""
    try:
        # Clear memory
        if session_id in session_memories:
            session_memories[session_id].clear()
        
        # Clear legacy session
        if session_id in chat_sessions:
            del chat_sessions[session_id]
            
        return jsonify({'message': 'Chat history cleared', 'session_id': session_id})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download generated files"""
    try:
        if os.path.exists(filename):
            return send_file(filename)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/', methods=['GET'])
def home():
    """Home page with API documentation"""
    return """
    <h1>🤖 Office Management Chatbot API</h1>
    <p>Welcome to the intelligent Office Management Assistant!</p>
    
    <h2>🚀 Chatbot Endpoints:</h2>
    <ul>
        <li><strong>POST /api/chat</strong> - Main chatbot conversation endpoint</li>
        <li><strong>GET /api/chat/history/&lt;session_id&gt;</strong> - Get chat history</li>
        <li><strong>DELETE /api/chat/clear/&lt;session_id&gt;</strong> - Clear chat history</li>
        <li><strong>GET /api/download/&lt;filename&gt;</strong> - Download generated files</li>
    </ul>
    
    <h2>💬 How to Use:</h2>
    <p>Send a POST request to <code>/api/chat</code> with:</p>
    <pre>
    {
        "message": "Your question or request here",
        "session_id": "optional_session_id"
    }
    </pre>
    
    <h2>🎯 What I Can Do:</h2>
    <ul>
        <li>Answer questions about employees, salaries, departments</li>
        <li>Generate salary slips for employees</li>
        <li>Provide general office management assistance</li>
        <li>Maintain conversation context across messages</li>
    </ul>
    
    <h2>📝 Example Messages:</h2>
    <ul>
        <li>"What is John Doe's salary?"</li>
        <li>"Generate salary slip for employee LWE103"</li>
        <li>"Show me all employees in IT department"</li>
        <li>"Create a salary slip for March 2025 for employee ADMIN1"</li>
    </ul>
    
    <hr>

    """

if __name__ == '__main__':
    app.run(debug=True, port=5000)

# from googletrans import LANGUAGES , Translator
# import asyncio

# # for lang_code , lang_name in LANGUAGES.items():
# #     print(f"{lang_code}:{lang_name}")

# ts = Translator()
# # tx = ""
# async def translate_text():
#     result = await ts.translate(text="अमनची जन्मतारीख काय आहे?", src='auto', dest='en')
#     print(result.text)

# # Run the async function
# asyncio.run(translate_text())