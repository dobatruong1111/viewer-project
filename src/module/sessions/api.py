from fastapi import APIRouter

import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from db.db import get_db
from .repository import SessionsRepository
from .schema import OutSessionSchema, InSessionSchema

router = APIRouter(prefix="/sessions", tags=['sessions'])
logger = logging.getLogger(__name__)

@router.get(
    "/{session_id}", status_code=status.HTTP_200_OK, response_model=OutSessionSchema
)
async def get_session_by_id(
    coupon_id: int, db: AsyncSession = Depends(get_db)
) -> OutSessionSchema:
    sessions_repository = SessionsRepository(db)
    session = await sessions_repository.get_by_id(coupon_id)
    return OutSessionSchema(**session.dict())

