import os
from operator import itemgetter
from dotenv import load_dotenv
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.documents import Document
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.agents import AgentAction
from langchain_core.runnables import RunnableBranch

# ============================================================================
# CONFIGURATION & INITIALIZATION
# ============================================================================

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not DATABASE_URL or not GOOGLE_API_KEY:
    raise ValueError("DATABASE_URL and GOOGLE_API_KEY must be set in the environment.")

# Configuration constants
LLM_MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL = "models/gemini-embedding-001"
SCHEMA_RETRIEVER_K = 3
TOP_K_RESULTS = 5

# Initialize core components
db = SQLDatabase.from_uri(DATABASE_URL)
llm = ChatGoogleGenerativeAI(model=LLM_MODEL, google_api_key=GOOGLE_API_KEY)
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)

# ============================================================================
# SCHEMA RETRIEVAL
# ============================================================================

def setup_schema_retriever():
    """Builds the FAISS vector store for fast retrieval of relevant table schemas."""
    documents = []
    try:
        for table_name in db.get_usable_table_names():
            table_info = db.get_table_info(table_names=[table_name])
            documents.append(Document(
                page_content=table_info,
                metadata={"name": table_name}
            ))
    except Exception as e:
        print(f"Error fetching table info: {e}")
        # Fallback to an empty list or handle the error gracefully
        return FAISS.from_documents([], embedding=embeddings).as_retriever(search_kwargs={"k": 3})

    vectorstore = FAISS.from_documents(documents, embedding=embeddings)
    return vectorstore.as_retriever(search_kwargs={"k": SCHEMA_RETRIEVER_K})

retriever = setup_schema_retriever()

def get_relevant_schema(input: str) -> str:
    """Retrieves relevant table schemas based on the input query."""
    relevant_docs = retriever.get_relevant_documents(input)
    return "\n\n".join([doc.page_content for doc in relevant_docs])

# ============================================================================
# ROUTER CHAIN - Classifies user input into query types
# ============================================================================

router_template = """
You are an intelligent router. Your task is to classify the user's input into one of three categories:

1. 'data_query': If the user is asking a question that requires running a SQL query to retrieve data from the database.
   Examples: "how many users are there?", "what is the average salary?", "list the top 5 products", "show me all orders from 2024"

2. 'schema_query': If the user is asking about the structure of the database, tables, columns, or relationships.
   Examples: "what tables are in the database?", "what columns does the 'employees' table have?", "show me the schema for the 'orders' table", "what's the structure of the database?"

3. 'general_chat': For any other question including greetings, general knowledge, small talk, or questions not related to the database.
   Examples: "hello", "what's the weather?", "tell me a joke", "how are you?"

IMPORTANT RULES:
- If uncertain, prefer 'data_query' over 'schema_query' (data queries are more common)
- If a question could be answered by looking at data, it's a 'data_query'
- If a question is specifically about database structure/metadata, it's a 'schema_query'
- Return ONLY the classification category as a single lowercase word: data_query, schema_query, or general_chat
- Do NOT include any explanation or additional text
"""

router_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", router_template),
        ("human", "{input}"),
    ]
)

router_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY, temperature=0.0)

router_chain = (
    {"input": itemgetter("input")}
    | router_prompt
    | router_llm
    | RunnableLambda(lambda x: x.content.strip().lower())
)

# ============================================================================
# SCHEMA QUERY CHAIN - Answers questions about database structure
# ============================================================================

def get_full_schema(_):
    """Retrieves the complete database schema."""
    return db.get_table_info(table_names=db.get_usable_table_names())

schema_query_template = """
You are a database schema expert. Your role is to help users understand the structure and organization of the database.

Using the database schema provided below, answer the user's question clearly and accurately.

DATABASE SCHEMA:
{schema_text}

GUIDELINES:
- Provide clear, concise answers about tables, columns, and relationships
- If the user asks about something not in the schema, say "This information is not available in the current schema"
- Format your response in a readable way (use bullet points or lists when appropriate)
- Be specific about data types and constraints when relevant
- Do NOT make up or assume information not in the schema
"""

schema_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", schema_query_template),
        ("human", "{input}"),
    ]
)

schema_chain = (
    RunnablePassthrough.assign(schema_text=RunnableLambda(get_full_schema))
    | schema_prompt
    | llm
    | RunnableLambda(lambda x: x.content)
)

# ============================================================================
# DATA QUERY CHAIN - Executes SQL queries against the database
# ============================================================================

data_query_template = """
You are an expert and secure SQL assistant. Your goal is to translate user questions
into efficient and safe SQL queries for a {dialect} database.

TASK:
1. Analyze the user's question carefully
2. Create a syntactically correct {dialect} query using the provided schema
3. Execute the query and examine the results
4. Provide a clear, natural language answer based on the results

IMPORTANT CONSTRAINTS:
- SECURITY: DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP, ALTER, etc.)
- SECURITY: Only SELECT queries are allowed
- PERFORMANCE: Limit results to at most {top_k} rows unless the user specifies otherwise
- PERFORMANCE: Only select relevant columns, never use SELECT *
- PERFORMANCE: Use appropriate WHERE clauses and indexes when possible
- ACCURACY: If the query fails, explain what went wrong and suggest alternatives

RESPONSE FORMAT:
- Provide the answer in natural language
- If the query returns no results, clearly state that
- If there's an error, explain it clearly
- Be concise but informative

RELEVANT DATABASE SCHEMA:
{{table_info}}
"""

data_query_template_FORMATTED = data_query_template.format(
    dialect=db.dialect,
    top_k=TOP_K_RESULTS
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", data_query_template_FORMATTED),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

tools = toolkit.get_tools()
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    return_intermediate_steps=True
)

data_query_executor_chain = (
    RunnablePassthrough.assign(table_info=itemgetter("input") | RunnableLambda(get_relevant_schema))
    | agent_executor
)

# ============================================================================
# GENERAL CHAT CHAIN - Handles non-database questions
# ============================================================================

general_chat_template = """
You are a helpful and friendly assistant for AskDB, a database query application.

CONTEXT:
- You are part of a system that helps users query and understand databases
- Users may ask you general questions, greetings, or questions not related to databases
- You should be conversational and helpful

GUIDELINES:
- Answer questions directly and concisely
- Be friendly and professional
- If the user asks about database-related topics, you can provide general guidance
- If the user asks something you're unsure about, be honest about the limitations
- Keep responses brief and to the point (unless more detail is requested)
- Do NOT pretend to have access to the database - you can only help with general knowledge

EXAMPLES OF APPROPRIATE RESPONSES:
- Greetings: "Hello! I'm here to help you query your database. What would you like to know?"
- General questions: Provide helpful, accurate information
- Database guidance: Offer general tips about databases and SQL
"""

chat_prompt = ChatPromptTemplate.from_messages([
        ("system", general_chat_template),
        ("human", "{input}")
    ])

general_chat_chain = (
    chat_prompt
    | llm
    | RunnableLambda(lambda x: x.content)
)

# ============================================================================
# EXECUTION FUNCTIONS
# ============================================================================

def extract_query_and_response(agent_output):
    """Extracts the final response and SQL query from the agent output."""
    final_response = agent_output.get("output", "Could not find final answer.")
    intermediate_steps = agent_output.get("intermediate_steps", [])
    sql_query = "SQL Query not found."
    for action, _ in intermediate_steps:
        if isinstance(action, AgentAction):
            if action.tool == 'sql_db_query':
                sql_query = action.tool_input.get('query', 'Query input key not found.')
                break

    return {
        "response": final_response,
        "sql_query": sql_query
    }

def run_database_query(input_dict: dict) -> dict:
    """Runs the data query path and extracts the structured result."""
    result = data_query_executor_chain.invoke({"input": input_dict['input']})
    structured_output = extract_query_and_response(result)
    return structured_output

def run_schema_query(input_dict: dict) -> dict:
    """Runs the schema query path to answer questions about database structure."""
    try:
        response = schema_chain.invoke({"input": input_dict['input']})
        return {
            "response": response,
        }
    except Exception as e:
        print(f"Error in Schema Query Path: {e}")
        raise

def run_general_chat(input_dict: dict) -> dict:
    """Runs the general chat path for non-database questions."""
    response = general_chat_chain.invoke({"input": input_dict['input']})
    return {
        "response": response,
    }

def get_final_response(input_dict: dict) -> dict:
    """Routes the input to the appropriate handler based on classification."""
    final_agent_chain = RunnablePassthrough.assign(
        route=router_chain
    ) | RunnableBranch(
        (lambda x: x["route"] == "data_query", RunnableLambda(run_database_query)),
        (lambda x: x["route"] == "schema_query", RunnableLambda(run_schema_query)),
        RunnableLambda(run_general_chat)
    )

    return final_agent_chain.invoke({"input": input_dict})
