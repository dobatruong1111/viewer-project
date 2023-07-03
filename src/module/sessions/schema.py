from typing import Optional, Any, Dict
from uuid import UUID

from pydantic import validator

from db.schema import BaseSchema

class SessionSchemaBase(BaseSchema):
    user_id : str
    session : str

    owner_session : str

    owner_user_id : str
    
    store_authentication : str
    
    store_url : str
    
    study_iuid : str
    
    expired_time : str

class InSessionSchema(SessionSchemaBase):
    ...

class SessionSchema(SessionSchemaBase):
    id: UUID

class OutSessionSchema(SessionSchema):
    ...