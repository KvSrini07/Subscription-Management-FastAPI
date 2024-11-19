 app/routers/router.py
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query
from app.configuration.db import ConnectionManager
from app.models.models import OrganizationEntity, UserEntity
from app.models.pydantic_models import Register, CreateUser, UpdateUser, ResponseBO, PageableResponse, CreateRole, \
    UpdatePermission
from app.services.permission_service import PermissionService
from app.services.user_service import UserService
from app.services.role_service import RoleService
from app.configuration.logger import setup_logger

role_router = APIRouter()

role_service = RoleService()

@role_router.post("/create", response_model=ResponseBO)
async def create_role(data: CreateRole):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request with data: {data}")

        # Check if the role already exists in the database
        conflict = await role_service.check_role_exists(data.role, logger)
        if conflict:
            raise HTTPException(status_code=409, detail=f"Role '{data.role}' already exists.")

        # Proceed with role creation if no conflict
        result = await role_service.create_role(data, logger)

        if not result:
            raise HTTPException(status_code=404, detail="Failed to create role")

        return ResponseBO(
            code=201,
            status="success",
            message="Role created successfully.",
            embedded=result  # Assuming result contains the created role information
        )

    except HTTPException as http_exc:
        logger.error(f"HTTPException occurred: {http_exc.detail}")
        raise http_exc
    except ValueError as ve:
        logger.error(f"ValueError occurred: {ve}")
        raise HTTPException(status_code=400, detail=f"Value error: {ve}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")

@role_router.put("/update/{role_id}", response_model=ResponseBO)
async def update_role(role_id: int, data: CreateRole):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    async with ConnectionManager() as session:
        try:
            logger.info(f"Received request to update role with ID {role_id} and data: {data}")

            # Check if the role already exists
            if await role_service.role_exists(session, data.role, role_id):
                logger.error(f"Conflict: Role '{data.role}' already exists.")
                raise HTTPException(status_code=409, detail=f"Role '{data.role}' already exists.")

            result = await role_service.update_role(role_id, data, logger)

            if not result:
                raise HTTPException(status_code=404, detail="Role not found or update failed")

            return ResponseBO(
                code=200,  # OK status code
                status="success",
                message="Role updated successfully.",
                embedded=result  # Assuming result contains the updated role information
            )

        except HTTPException as http_exc:
            logger.error(f"HTTPException occurred: {http_exc.detail}")
            raise http_exc
        except ValueError as ve:
            logger.error(f"ValueError occurred: {ve}")
            raise HTTPException(status_code=400, detail=f"Value error: {ve}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")


@role_router.get("/get/{role_id}", response_model=ResponseBO)
async def get_role_by_id(role_id: int):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request to get role with ID {role_id}")
        result = await role_service.get_role_by_id(role_id, logger)

        if not result:
            raise HTTPException(status_code=404, detail="Role not found")

        return ResponseBO(
            code=200,  # OK status code
            status="success",
            message="Role retrieved successfully.",
            embedded=result  # Assuming result contains the role information
        )

    except HTTPException as http_exc:
        logger.error(f"HTTPException occurred: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")

@role_router.get("/get-role-by-user/{user_id}", response_model=ResponseBO)
async def get_role_by_user_id(user_id: int):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request to get role for user with ID {user_id}")
        result = await role_service.get_role_by_user_id(user_id, logger)

        if not result:
            raise HTTPException(status_code=404, detail="Role not found for the specified user")

        return ResponseBO(
            code=200,  # OK status code
            status="success",
            message="Role retrieved successfully.",
            embedded=result  # Assuming result contains the role information
        )

    except HTTPException as http_exc:
        logger.error(f"HTTPException occurred: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")


@role_router.get("/get_all", response_model=ResponseBO)
async def get_all_roles():
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info("Received request to get all roles")
        result = await role_service.get_all_roles(logger)

        return ResponseBO(
            code=200,  # OK status code
            status="success",
            message="Roles retrieved successfully.",
            embedded=result  # Assuming result contains the list of role information
        )

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")

@role_router.delete("/delete/{role_id}", response_model=ResponseBO)
async def delete_role(role_id: int):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request to delete role with ID {role_id}")

        # Check if the role is assigned to any users
        conflict = await role_service.check_role_assigned_to_users(role_id, logger)
        if conflict:
            raise HTTPException(status_code=409, detail="Role is assigned to users and cannot be deleted.")

        # Proceed with deletion if no conflict
        result = await role_service.delete_role(role_id, logger)

        if not result:
            raise HTTPException(status_code=404, detail="Role not found or delete failed")

        return ResponseBO(
            code=200,
            status="success",
            message="Role deleted successfully.",
            embedded=None  # No additional data needed for delete response
        )

    except HTTPException as http_exc:
        logger.error(f"HTTPException occurred: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")



user_router = APIRouter()

user_service = UserService()

@user_router.post("/register", response_model=ResponseBO)
async def register_user(data: Register):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    async with ConnectionManager() as session:
        try:
            logger.info(f"Received registration request with data: {data}")

            # Check if any values already exist
            checks = {
                "email_id": data.email_id,
                "mobile_no": data.mobile_no,
                "gstin": data.organization.gstin,
                "pan": data.organization.pan,
                "tan": data.organization.tan,
                "cin": data.organization.cin
            }

            # Check email and mobile in UserEntity
            for field, identifier in checks.items():
                if field in ["email_id", "mobile_no"] and await user_service.is_user_identifier_exists(session, logger, identifier, field):
                    logger.warning(f"{field.replace('_', ' ').title()} already exists: {identifier}")
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                        detail=f"{field.replace('_', ' ').title()} already exists")

            # Check GSTIN, PAN, TAN, and CIN in OrganizationEntity
            for field, identifier in checks.items():
                if field in ["gstin", "pan", "tan", "cin"] and await user_service.is_organization_identifier_exists(session, logger, identifier, field):
                    logger.warning(f"{field.upper()} already exists: {identifier}")
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"{field.upper()} already exists")

            user = await user_service.register(data, logger)  # Call the register function

            return ResponseBO(
                code=201,
                status="success",
                message="User registered successfully.",
                embedded=user  # or wrap user in another object if needed
            )

        except HTTPException as http_exc:
            logger.error(f"HTTPException occurred: {http_exc.detail}")
            raise http_exc
        except ValueError as ve:
            logger.error(f"ValueError occurred: {ve}")
            raise HTTPException(status_code=400, detail=f"Value error: {ve}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")

@user_router.post("/create", response_model=ResponseBO)
async def create_user(data: CreateUser):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    async with ConnectionManager() as session:
        try:
            logger.info(f"Received create request with data: {data}")

            # Check if any values already exist
            checks = {
                "email_id": data.email_id,
                "mobile_no": data.mobile_no
            }

            # Check email and mobile in UserEntity
            for field, identifier in checks.items():
                if field in ["email_id", "mobile_no"] and await user_service.is_user_identifier_exists(session, logger,
                                                                                                       identifier,
                                                                                                       field):
                    logger.warning(f"{field.replace('_', ' ').title()} already exists: {identifier}")
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                        detail=f"{field.replace('_', ' ').title()} already exists")

            user = await user_service.create_user(data, logger)  # Call the create_user function

            return ResponseBO(
                code=201,
                status="success",
                message="User created successfully.",
                embedded=user  # or wrap user in another object if needed
            )

        except HTTPException as http_exc:
            logger.error(f"HTTPException occurred: {http_exc.detail}")
            raise http_exc
        except ValueError as ve:
            logger.error(f"ValueError occurred: {ve}")
            raise HTTPException(status_code=400, detail=f"Value error: {ve}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")

@user_router.put("/update/{user_id}", response_model=ResponseBO)
async def update_user(user_id: int, data: UpdateUser):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    async with ConnectionManager() as session:
        try:
            logger.info(f"Received update request for user_id: {user_id} with data: {data}")

            # Fetch the existing user
            existing_user = await user_service.fetch_existing_user(session, user_id, logger)

            if not existing_user:
                logger.error(f"User not found: {user_id}")
                raise HTTPException(status_code=404, detail="User not found.")

            # Check for mobile number uniqueness
            if not await user_service.check_unique_value(session, UserEntity, 'mobile_no', data.mobile_no, exclude_id=user_id):
                logger.error(f"Mobile number already exists: {data.mobile_no}")
                raise HTTPException(status_code=409, detail="Mobile number already exists.")

            # Check for organization-related fields if organization data is provided
            if data.organization:
                organization_fields = ['gstin', 'pan', 'tan', 'cin']
                for field in organization_fields:
                    value = getattr(data.organization, field, None)
                    if not await user_service.check_unique_value(session, OrganizationEntity, field, value, exclude_id=existing_user.organization_id):
                        logger.error(f"{field.upper()} already exists: {value}")
                        raise HTTPException(status_code=409, detail=f"{field.upper()} already exists.")

            # Call the update_user function and get the updated user information
            updated_user = await user_service.update_user(user_id, data, logger)

            return ResponseBO(
                code=200,
                status="success",
                message="User updated successfully.",
                embedded=updated_user  # or wrap updated_user in another object if needed
            )

        except HTTPException as http_exc:
            logger.error(f"HTTPException occurred: {http_exc.detail}")
            raise http_exc
        except ValueError as ve:
            logger.error(f"ValueError occurred: {ve}")
            raise HTTPException(status_code=400, detail=f"Value error: {ve}")
        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")


@user_router.get("/get/{user_id}", response_model=ResponseBO)
async def get_user(user_id: int):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request to fetch user by ID: {user_id}")
        user = await user_service.get_by_id(user_id, logger)

        if user is None:
            logger.warning(f"No user found with ID: {user_id}")
            return ResponseBO(
                code=404,
                status="failure",
                message="User not found",
                embedded=None
            )

        return ResponseBO(
            code=200,
            status="success",
            message="User found",
            embedded=user  # or wrap user in another object if needed
        )

    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")

@user_router.get("/get/username/{username}", response_model=ResponseBO)
async def get_user_by_username(username: str):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request to fetch user by username: {username}")
        user = await user_service.get_by_username(username, logger)

        if user is None:
            logger.warning(f"No user found with username: {username}")
            return ResponseBO(
                code=404,
                status="failure",
                message="User not found",
                embedded=None
            )

        return ResponseBO(
            code=200,
            status="success",
            message="User found",
            embedded=user  # or wrap user in another object if needed
        )

    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")

@user_router.get("/get/role/{role_id}", response_model=ResponseBO)
async def get_user_by_role_id(role_id: int):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request to fetch users by role ID: {role_id}")
        users = await user_service.get_by_role_id(role_id, logger)

        if not users:
            logger.warning(f"No users found with role ID: {role_id}")
            return ResponseBO(
                code=404,
                status="failure",
                message="No users found for the given role ID",
                embedded=None
            )

        return ResponseBO(
            code=200,
            status="success",
            message="Users found",
            embedded=users  # Wrap users in another object if needed
        )

    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")


@user_router.get("/get_all", response_model=PageableResponse)
async def get_all_users(
    size: int = Query(10, description="Number of users per page"),
    page: int = Query(1, description="Page number"),
    search_key: Optional[str] = Query(None, description="Search keyword")
):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request to fetch all users - page: {page}, size: {size}, searchKey: {search_key}")
        # Fetch paginated users
        paginated_data = await user_service.get_all(logger, page, size, search_key)

        if not paginated_data["data"]:
            logger.warning("No users found")

        # Return paginated response
        return PageableResponse(
            code=200,
            status="success",
            page=page,
            size=size,
            embedded=paginated_data["data"],  # Users DTOs
            message="Fetched all users successfully",
            totalPages=paginated_data["total_pages"],
            totalElements=paginated_data["total_elements"]
        )

    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")


@user_router.delete("/delete/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(user_id: int):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request to delete user with ID: {user_id}")
        # Call the delete_user function
        await user_service.delete_user(user_id, logger)

        return ResponseBO(
            code=200,
            status="success",
            message=f"User with ID {user_id} has been successfully deleted.",
            embedded=None
        )

    except HTTPException as http_exc:
        logger.error(f"HTTPException occurred: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"An unexpected error occurred while deleting user: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")

permission_router = APIRouter()

permission_service = PermissionService()

@permission_router.put("/update/{permission_id}", response_model=ResponseBO)
async def update_permission(permission_id: int, data: UpdatePermission):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    async with ConnectionManager() as session:
        try:
            logger.info(f"Received request to update permission with ID {permission_id} and data: {data}")

            # Check if the permission already exists
            # if await permission_service.permission_exists(session, data.name, permission_id):
            #     logger.error(f"Conflict: Permission '{data.name}' already exists.")
            #     raise HTTPException(status_code=409, detail=f"Permission '{data.name}' already exists.")

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


@permission_router.get("/get_all", response_model=PageableResponse)
async def get_all_permissions(
        size: int = Query(10, description="Number of permissions per page"),
        page: int = Query(1, description="Page number"),
        search_key: Optional[str] = Query(None, description="Search keyword")
):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request to fetch all permissions - page: {page}, size: {size}, searchKey: {search_key}")

        # Fetch paginated permissions
        paginated_data = await permission_service.get_all(logger, page, size, search_key)

        if not paginated_data["data"]:
            logger.warning("No permissions found")

        # Return paginated response
        return PageableResponse(
            code=200,
            status="success",
            page=page,
            size=size,
            embedded=paginated_data["data"],  # Permissions DTOs
            message="Fetched all permissions successfully",
            totalPages=paginated_data["total_pages"],
            totalElements=paginated_data["total_elements"]
        )

    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
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
