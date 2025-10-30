from fastapi import APIRouter
from ..controllers import query_controllers

router = APIRouter()

router.include_router(query_controllers.router)