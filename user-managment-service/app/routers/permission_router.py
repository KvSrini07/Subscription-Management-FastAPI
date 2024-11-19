# app/routers/permission_router.py

import uuid
import asyncpg
from fastapi import APIRouter, HTTPException
from app.configuration.db import ConnectionManager
from app.models.pydantic_models import UpdatePermission
from app.models.response import ResponseBO
from app.services import permission_service
from app.configuration.logger import setup_logger

permission_router = APIRouter()

@permission_router.put("/update/{permission_id}", response_model=ResponseBO)
async def update_permission(permission_id: int, data: UpdatePermission):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    async with ConnectionManager() as session:
        try:
            logger.info(f"Received request to update permission with ID {permission_id} and data: {data}")

            # Check if the permission already exists
            if await permission_service.permission_exists(session, data.permission_name, permission_id):
                logger.error(f"Conflict: Permission '{data.permission_name}' already exists.")
                raise HTTPException(status_code=409, detail=f"Permission '{data.permission_name}' already exists.")

            result = await permission_service.update_permission(permission_id, data, logger)

            if not result:
                raise HTTPException(status_code=404, detail="Permission not found or update failed")

            return ResponseBO(
                code=200,  # OK status code
                status="success",
                message="Permission updated successfully.",
                embedded=result  # Assuming result contains the updated permission information
            )

        except HTTPException as http_exc:
            logger.error(f"HTTPException occurred: {http_exc.detail}")
            raise http_exc
        except ValueError as ve:
            logger.error(f"ValueError occurred: {ve}")
            raise HTTPException(status_code=400, detail=f"Value error: {ve}")
        except asyncpg.PostgresError as pg_exc:
            logger.error(f"Database error occurred: {pg_exc}")
            raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")

@permission_router.get("/get/{permission_id}", response_model=ResponseBO)
async def get_permission(permission_id: int):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    async with ConnectionManager() as session:
        try:
            logger.info(f"Received request to get permission with ID {permission_id}")

            # Fetch the permission by ID
            permission_dto = await permission_service.get_permission_by_id(permission_id, session, logger)

            if not permission_dto:
                raise HTTPException(status_code=404, detail="Permission not found")

            return ResponseBO(
                code=200,
                status="success",
                message="Permission retrieved successfully.",
                embedded=permission_dto  # Return the permission DTO in the response
            )

        except HTTPException as http_exc:
            logger.error(f"HTTPException occurred: {http_exc.detail}")
            raise http_exc
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")

@permission_router.delete("/delete/{permission_id}", response_model=ResponseBO)
async def delete_permission(permission_id: int):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request to delete permission with ID {permission_id}")

        # Check if the permission is assigned to any users
        conflict = await permission_service.check_permission_assigned_to_users(permission_id, logger)
        if conflict:
            raise HTTPException(status_code=409, detail="Permission is assigned to users and cannot be deleted.")

        # Proceed with deletion if no conflict
        result = await permission_service.delete_permission(permission_id, logger)

        if not result:
            raise HTTPException(status_code=404, detail="Permission not found or delete failed")

        return ResponseBO(
            code=200,
            status="success",
            message="Permission deleted successfully.",
            embedded=None  # No additional data needed for delete response
        )

    except HTTPException as http_exc:
        logger.error(f"HTTPException occurred: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")
