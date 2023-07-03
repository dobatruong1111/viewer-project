from typing import Type

from db.repository.base_repository import BaseRepository
from .model import Session
from .schema import InSessionSchema, SessionSchema


class SessionsRepository(BaseRepository[InSessionSchema, SessionSchema, Session]):
    @property
    def _in_schema(self) -> Type[InSessionSchema]:
        return InSessionSchema

    @property
    def _schema(self) -> Type[SessionSchema]:
        return SessionSchema

    @property
    def _table(self) -> Type[Session]:
        return Session