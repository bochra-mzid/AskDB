# AskDB

AskDB is an intelligent database query interface that allows users to ask natural language questions about their database and receive SQL queries and results. It uses AI-powered routing to handle data queries, schema questions, and general chat.


## Architecture & Approach

### System Architecture

![System Architecture](./frontend/media/architecture.png)

### Intent Router

Not every user input is a data query. The system classifies user intent to route requests appropriately:

- **Data Query**: "Show me last week's sales" → SQL generation and execution
- **Schema Query**: "What columns are in the users table?" → Schema information
- **General Chat**: "Hello" → Conversational response

**How it works**: The router uses an LLM with a specialized prompt to classify incoming questions into one of three categories to direct the input to the appropriate path:

1. **Classification Process**:
   - User question is sent to the router LLM with a specialized classification prompt
   - The prompt contains clear definitions and examples for each category
   - The LLM analyzes the question and returns the classification (data_query, schema_query, or general_chat)

2. **Routing Logic**:
   - **data_query** → Triggers the full SQL pipeline (metadata retrieval → SQL generation → execution → synthesis)
   - **schema_query** → Retrieves full database schema and answers structural questions
   - **general_chat** → Generates conversational responses without database access

### Dynamic Metadata Retrieval (RAG)

Instead of overwhelming the LLM with the entire database schema, the system dynamically retrieves only relevant context:

1. **Embeddings**: Table and column descriptions are converted to embeddings using Google's Generative AI embeddings model
2. **Vector Search**: User questions are embedded and matched against schema embeddings using FAISS
3. **Selective Context**: Only the top-k most relevant tables/columns are passed to the SQL generation prompt

**How it works**: When a data query is detected, the system:
- Converts the user's question into an embedding vector
- Searches the FAISS vector store to find the most semantically similar table schemas
- Passes only these relevant schemas to the SQL generator, not the entire database schema

### LangChain SQL Agent

The system uses a LangChain Tool-Calling Agent with the SQLDatabaseToolkit to interact with the database:

1. **Agent Setup**: A tool-calling agent is created using `create_tool_calling_agent` with access to SQL database tools
2. **Available Tools**: The agent has access to tools for querying the database, checking table info, and validating queries
3. **Execution Flow**: The AgentExecutor manages the agent's reasoning loop, it can make multiple tool calls to refine queries and handle errors
4. **Security**: The agent is constrained to SELECT queries only, preventing any data modification (INSERT, UPDATE, DELETE, DROP)

**How it works**: When processing a data query:
- The agent receives the user's question along with relevant schema context
- It reasons about which SQL query to execute using the available tools
- The agent can iteratively refine its approach if a query fails
- Final results are extracted from the agent's intermediate steps and formatted as a response

### Results Synthesis

After query execution, the system synthesizes results into natural language:

- Converts raw database results into human-readable answers
- Maintains context from the original question
- Provides accurate, concise responses

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **LangChain** - LLM orchestration and SQL toolkit
- **Google Generative AI** - LLM and embeddings
- **FAISS** - Vector store for schema retrieval
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Database

### Frontend
- **React** - UI library
- **TypeScript** - Type-safe JavaScript
- **Vite** - Fast build tool and dev server
- **Material-UI** - Component library
- **pnpm** - Package manager

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL database
- Google API Key (for Gemini LLM)
- pnpm (install with `npm install -g pnpm`)

### Environment Setup

Create a `.env` file in the `backend` directory:

```
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
GOOGLE_API_KEY=your_google_api_key_here
```

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
pnpm install
pnpm dev
```

The frontend will be available at `http://localhost:5173`

## API Endpoints

### POST /ask
Submit a natural language question and get SQL + results.

**Request:**
```json
{
  "question": "How many users are in the database?"
}
```

**Response:**
```json
{
  "query": "SELECT COUNT(*) FROM users;",
  "response": "There are 100 users in the database."
}
```

## Configuration

Key configuration in `backend/app/services/sql_service.py`:
- `LLM_MODEL`: Gemini model version
- `SCHEMA_RETRIEVER_K`: Number of schema results to retrieve
- `TOP_K_RESULTS`: Number of query results to return


