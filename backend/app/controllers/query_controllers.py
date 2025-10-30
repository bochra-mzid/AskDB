
from fastapi import APIRouter, HTTPException
from ..schemas import QueryRequest, QueryResponse
from ..services.sql_service import get_final_response

router = APIRouter()

@router.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """
    Process a natural language question and route it to the appropriate handler.
    Can handle data queries (SQL), schema questions, or general chat.
    Returns the SQL query (if applicable) and the response.
    """
    try:
        response = get_final_response(request.question)
        return QueryResponse(
            query=response.get("sql_query"),
            response=response.get("response")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

