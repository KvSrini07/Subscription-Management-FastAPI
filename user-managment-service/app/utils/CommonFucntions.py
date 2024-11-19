from typing import Type, TypeVar, Generic
from pydantic import BaseModel
from sqlalchemy.ext.declarative import as_declarative, declared_attr

# Type variables for generic usage
T = TypeVar('T', bound=BaseModel)  # For Pydantic models
R = TypeVar('R')  # For ORM models

def orm_to_pydantic(orm_instance: R, pydantic_model: Type[T]) -> T:
    print(orm_instance)
    """Converts an ORM instance to a Pydantic model."""
    data = {}
    for column in orm_instance.__table__.columns:
        value = getattr(orm_instance, column.name)
        # Handle None value for status field explicitly
        if column.name == "status" and value is None:
            value = False  # Defaulting None to False
        data[column.name] = value
    return pydantic_model(**data)
