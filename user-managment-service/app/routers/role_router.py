 # app/routers/role_router.py
#
# import uuid
# import asyncpg
# from fastapi import APIRouter, HTTPException
# from app.configuration.db import ConnectionManager
# from app.models.pydantic_models import CreateRole
# from app.models.response import ResponseBO
# from app.services import role_service
# from app.configuration.logger import setup_logger
#
# role_router = APIRouter()
#
# @role_router.post("/create", response_model=ResponseBO)
# async def create_role(data: CreateRole):
#     worker_id = str(uuid.uuid4())  # Generate a unique worker_id
#     logger = setup_logger(worker_id)  # Set up logging with the worker_id
#
#     try:
#         logger.info(f"Received request with data: {data}")
#
#         # Check if the role already exists in the database
#         conflict = await role_service.check_role_exists(data.role, logger)
#         if conflict:
#             raise HTTPException(status_code=409, detail=f"Role '{data.role}' already exists.")
#
#         # Proceed with role creation if no conflict
#         result = await role_service.create_role(data, logger)
#
#         if not result:
#             raise HTTPException(status_code=404, detail="Failed to create role")
#
#         return ResponseBO(
#             code=201,
#             status="success",
#             message="Role created successfully.",
#             embedded=result  # Assuming result contains the created role information
#         )
#
#     except HTTPException as http_exc:
#         logger.error(f"HTTPException occurred: {http_exc.detail}")
#         raise http_exc
#     except ValueError as ve:
#         logger.error(f"ValueError occurred: {ve}")
#         raise HTTPException(status_code=400, detail=f"Value error: {ve}")
#     except asyncpg.PostgresError as pg_exc:
#         logger.error(f"Database error occurred: {pg_exc}")
#         raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
#     except Exception as e:
#         logger.error(f"An unexpected error occurred: {e}")
#         raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")
#
# @role_router.put("/update/{role_id}", response_model=ResponseBO)
# async def update_role(role_id: int, data: CreateRole):
#     worker_id = str(uuid.uuid4())  # Generate a unique worker_id
#     logger = setup_logger(worker_id)  # Set up logging with the worker_id
#
#     async with ConnectionManager() as session:
#         try:
#             logger.info(f"Received request to update role with ID {role_id} and data: {data}")
#
#             # Check if the role already exists
#             if await role_service.role_exists(session, data.role, role_id):
#                 logger.error(f"Conflict: Role '{data.role}' already exists.")
#                 raise HTTPException(status_code=409, detail=f"Role '{data.role}' already exists.")
#
#             result = await role_service.update_role(role_id, data, logger)
#
#             if not result:
#                 raise HTTPException(status_code=404, detail="Role not found or update failed")
#
#             return ResponseBO(
#                 code=200,  # OK status code
#                 status="success",
#                 message="Role updated successfully.",
#                 embedded=result  # Assuming result contains the updated role information
#             )
#
#         except HTTPException as http_exc:
#             logger.error(f"HTTPException occurred: {http_exc.detail}")
#             raise http_exc
#         except ValueError as ve:
#             logger.error(f"ValueError occurred: {ve}")
#             raise HTTPException(status_code=400, detail=f"Value error: {ve}")
#         except asyncpg.PostgresError as pg_exc:
#             logger.error(f"Database error occurred: {pg_exc}")
#             raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
#         except Exception as e:
#             logger.error(f"An unexpected error occurred: {e}")
#             raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")
#
#
# @role_router.get("/get/{role_id}", response_model=ResponseBO)
# async def get_role_by_id(role_id: int):
#     worker_id = str(uuid.uuid4())  # Generate a unique worker_id
#     logger = setup_logger(worker_id)  # Set up logging with the worker_id
#
#     try:
#         logger.info(f"Received request to get role with ID {role_id}")
#         result = await role_service.get_role_by_id(role_id, logger)
#
#         if not result:
#             raise HTTPException(status_code=404, detail="Role not found")
#
#         return ResponseBO(
#             code=200,  # OK status code
#             status="success",
#             message="Role retrieved successfully.",
#             embedded=result  # Assuming result contains the role information
#         )
#
#     except HTTPException as http_exc:
#         logger.error(f"HTTPException occurred: {http_exc.detail}")
#         raise http_exc
#     except Exception as e:
#         logger.error(f"An unexpected error occurred: {e}")
#         raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")
#
# @role_router.get("/get_all", response_model=ResponseBO)
# async def get_all_roles():
#     worker_id = str(uuid.uuid4())  # Generate a unique worker_id
#     logger = setup_logger(worker_id)  # Set up logging with the worker_id
#
#     try:
#         logger.info("Received request to get all roles")
#         result = await role_service.get_all_roles(logger)
#
#         return ResponseBO(
#             code=200,  # OK status code
#             status="success",
#             message="Roles retrieved successfully.",
#             embedded=result  # Assuming result contains the list of role information
#         )
#
#     except Exception as e:
#         logger.error(f"An unexpected error occurred: {e}")
#         raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")
#
# @role_router.delete("/delete/{role_id}", response_model=ResponseBO)
# async def delete_role(role_id: int):
#     worker_id = str(uuid.uuid4())  # Generate a unique worker_id
#     logger = setup_logger(worker_id)  # Set up logging with the worker_id
#
#     try:
#         logger.info(f"Received request to delete role with ID {role_id}")
#
#         # Check if the role is assigned to any users
#         conflict = await role_service.check_role_assigned_to_users(role_id, logger)
#         if conflict:
#             raise HTTPException(status_code=409, detail="Role is assigned to users and cannot be deleted.")
#
#         # Proceed with deletion if no conflict
#         result = await role_service.delete_role(role_id, logger)
#
#         if not result:
#             raise HTTPException(status_code=404, detail="Role not found or delete failed")
#
#         return ResponseBO(
#             code=200,
#             status="success",
#             message="Role deleted successfully.",
#             embedded=None  # No additional data needed for delete response
#         )
#
#     except HTTPException as http_exc:
#         logger.error(f"HTTPException occurred: {http_exc.detail}")
#         raise http_exc
#     except Exception as e:
#         logger.error(f"An unexpected error occurred: {e}")
#         raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")
#
#
