# app/routers/subscription_router.py

import uuid

import asyncpg
from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.models.pydantic_models import CreateSubscription, CreateService, CreateSubscriptionServiceMapping, \
    CreateApiPermission, CreateServiceApiPermissionMapping, PagePermissionDTO, PagePermissionCreateDTO, \
    ServiceApiPagePermissionsMappingCreateDTO
from app.models.response import ResponseBO
from app.configuration.logger import setup_logger
from app.services import subscription_service

subscription_router = APIRouter()


@subscription_router.post("/create", response_model=ResponseBO)
async def create_subscription(data: CreateSubscription):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request with data: {data}")

        # Check if the subscription name already exists
        existing_subscription = await subscription_service.check_subscription_name_exists(data.name, logger)
        if existing_subscription:
            # raise HTTPException(status_code=409, detail="Subscription name already exists")
            return ResponseBO(
            code=409,
            status="CONFLICT",
            data=None,
            message=f"Subscription name: '{data.name}' already exists for another subscription"
        )

        result = await subscription_service.create_subscription(data, logger)

        if not result:
            raise HTTPException(status_code=404, detail="Failed to create subscription")

        # Create and return a ResponseBO
        response = ResponseBO(
            code=201,  # HTTP status code for Created
            status="CREATED",
            data=result,
            message="Subscription created successfully."
        )
        return response

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


@subscription_router.put("/update/{subscription_id}", response_model=ResponseBO)
async def update_subscription(subscription_id: int, data: CreateSubscription):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request to update subscription ID {subscription_id} with data: {data}")

        # Check if the subscription name already exists for another subscription
        existing_subscription = await subscription_service.check_update_subscription_name_exists(data.name, subscription_id, logger)
        if existing_subscription:
            # raise HTTPException(status_code=409, detail="Subscription name already exists for another subscription")
            return ResponseBO(
                code=409,
                status="CONFLICT",
                data=None,
                message=f"Subscription name: '{data.name}' already exists for another subscription"
            )

        result = await subscription_service.update_subscription(subscription_id, data, logger)

        if not result:
            # raise HTTPException(status_code=404, detail="Failed to update subscription")
            logger.error(f"Subscription with ID {subscription_id} not found.")
            return ResponseBO(
                code=404,
                status="NOT FOUND",
                data=None,
                message=f"Subscription with ID {subscription_id} not found."
            )

        # Create and return a ResponseBO
        response = ResponseBO(
            code=200,  # HTTP status code for OK
            status="UPDATED",
            data=result,
            message="Subscription updated successfully."
        )
        return response

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


# @subscription_router.get("/get/{subscription_id}", response_model=ResponseBO)
# async def get_subscription(subscription_id: int):
#     worker_id = str(uuid.uuid4())  # Generate a unique worker_id
#     logger = setup_logger(worker_id)  # Set up logging with the worker_id
#
#     try:
#         logger.info(f"Received request to get subscription ID {subscription_id}")
#         result = await subscription_service.get_subscription_by_id(subscription_id, logger)
#
#         # Create and return a ResponseBO
#         response = ResponseBO(
#             code=200,  # HTTP status code for OK
#             status="success",
#             data=result,
#             message="Subscription retrieved successfully."
#         )
#         return response
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


#After add responseBO

@subscription_router.get("/get/{subscription_id}", response_model=ResponseBO)
async def get_subscription(subscription_id: int):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request to get subscription ID {subscription_id}")

        # Validate if subscription_id is a positive number
        if subscription_id <= 0:
            logger.error(f"Invalid subscription ID: {subscription_id}")
            return ResponseBO(
                code=400,
                status="BAD REQUEST",
                data=None,
                message="Subscription ID must be greater than 0."
            )

        # Fetch the subscription from the service
        result = await subscription_service.get_subscription_by_id(subscription_id, logger)

        # Check if subscription exists
        if not result:
            logger.error(f"Subscription with ID {subscription_id} not found.")
            return ResponseBO(
                code=404,
                status="NOT FOUND",
                data=None,
                message=f"Subscription with ID {subscription_id} not found."
            )

        # Create and return a success ResponseBO
        response = ResponseBO(
            code=200,
            status="OK",
            data=result,
            message="Subscription retrieved successfully."
        )
        return response

    except asyncpg.PostgresError as pg_exc:
        logger.error(f"Database error occurred: {pg_exc}")
        return ResponseBO(
            code=500,
            status="ERROR",
            data=None,
            message="Database error occurred. Please try again later."
        )

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return ResponseBO(
            code=500,
            status="ERROR",
            data=None,
            message="An unexpected error occurred. Please try again later."
        )


@subscription_router.get("/get_all", response_model=ResponseBO)
async def get_all_subscriptions():
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info("Received request to get all subscriptions")
        results = await subscription_service.get_all_subscriptions(logger)


        if not results:
            return ResponseBO(
            code=204,  # HTTP status code for OK
            status="NO CONTENT",
            data=results,
            message="No subscriptions found"
        )

        # Create and return a ResponseBO
        response = ResponseBO(
            code=200,  # HTTP status code for OK
            status="LIST RETRIEVED",
            data=results,
            message=f"{len(results)} Subscriptions retrieved successfully."
        )
        return response

    except asyncpg.PostgresError as pg_exc:
        logger.error(f"Database error occurred: {pg_exc}")
        raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")

@subscription_router.delete("/delete/{subscription_id}", response_model=ResponseBO)
async def handle_delete_subscription(subscription_id: int):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request to delete subscription ID {subscription_id}")
        subscription = await subscription_service.delete_subscription(subscription_id, logger)
        if not subscription:
            return ResponseBO(
                code=404,
                status="NOT FOUND",
                data=None,
                message=f"Subscription with ID {subscription_id} not found."
            )

        # Create and return a ResponseBO
        response = ResponseBO(
            code=200,
            status="DELETED",
            data=None,
            message="Subscription deleted successfully."
        )
        return response

    except HTTPException as http_exc:
        logger.error(f"HTTPException occurred: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")


@subscription_router.get("/getAllActive", response_model=ResponseBO)
async def get_all_active_subscriptions():
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info("Received request to get active subscriptions")
        results = await subscription_service.get_active_subscriptions(logger)
        if not results:
            return ResponseBO(
                code=204,  # HTTP status code for OK
                status="NO CONTENT",
                data=results,
                message="No Active subscriptions found"
            )
        # Create and return a ResponseBO
        response = ResponseBO(
            code=200,  # HTTP status code for OK
            status="LIST RETRIEVED",
            data=results,
            message="Active subscriptions retrieved successfully."
        )
        return response

    except asyncpg.PostgresError as pg_exc:
        logger.error(f"Database error occurred: {pg_exc}")
        raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")


# @subscription_router.post("/service/create", response_model=ResponseBO)
# async def create_service(data: CreateService):
#     worker_id = str(uuid.uuid4())  # Generate a unique worker_id
#     logger = setup_logger(worker_id)  # Set up logging with the worker_id
#
#     try:
#         logger.info(f"Received request with data: {data}")
#
#         # Check if the service name already exists
#         existing_service = await subscription_service.check_service_name_exists(data.name, logger)
#         if existing_service:
#             # raise HTTPException(status_code=409, detail="Service name already exists")
#             return ResponseBO(
#                 code=409,
#                 status="CONFLICT",
#                 data=None,
#                 message=f"Service name: '{data.name}' already exists for another service"
#             )
#
#         result = await subscription_service.create_service(data, logger)
#
#         if not result:
#             raise HTTPException(status_code=404, detail="Failed to create service")
#
#         # Create and return a ResponseBO
#         response = ResponseBO(
#             code=201,  # HTTP status code for Created
#             status="CREATED",
#             data=result,
#             message="Service created successfully."
#         )
#         return response
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
@subscription_router.post("/service/create", response_model=ResponseBO)
async def create_service(data: CreateService):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request with data: {data}")

        # Check if the service name already exists
        existing_service = await subscription_service.check_service_name_exists(data.name, logger)
        if existing_service:
            return ResponseBO(
                code=409,
                status="CONFLICT",
                data=None,
                message=f"Service name: '{data.name}' already exists for another service"
            )

        # Validate subscription_id
        subscription_exists = await subscription_service.check_subscription_exists(data.subscription_id, logger)
        if not subscription_exists:
            return ResponseBO(
                code=404,
                status="NOT FOUND",
                data=None,
                message=f"Subscription with ID {data.subscription_id} not found."
            )

        # Validate api_permission_ids if provided
        invalid_permissions = await subscription_service.validate_api_permissions(data.api_permission_id, logger)
        if invalid_permissions:
            return ResponseBO(
                code=404,
                status="NOT FOUND",
                data=None,
                message=f"Invalid API permission IDs: {invalid_permissions}."
            )

        # Create the service
        result = await subscription_service.create_service(data, logger)

        if not result:
            return ResponseBO(
                code=404,
                status="NOT FOUND",
                data=None,
                message="Failed to create service."
            )

        # Return success response
        response = ResponseBO(
            code=201,
            status="CREATED",
            data=result,
            message="Service created successfully."
        )
        return response

    except ValueError as ve:
        logger.error(f"ValueError occurred: {ve}")
        return ResponseBO(
            code=400,
            status="error",
            data=None,
            message=f"Value error: {ve}"
        )

    except asyncpg.PostgresError as pg_exc:
        logger.error(f"Database error occurred: {pg_exc}")
        return ResponseBO(
            code=500,
            status="error",
            data=None,
            message="Database error occurred. Please try again later."
        )

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return ResponseBO(
            code=500,
            status="error",
            data=None,
            message="An unexpected error occurred. Please try again later."
        )

@subscription_router.get("/service/get/{service_id}", response_model=ResponseBO)
async def get_service(service_id: int):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request to get service ID {service_id}")
        result = await subscription_service.get_service_by_id(service_id, logger)
        if not result:
            return ResponseBO(
                code=404,
                status="NOT FOUND",
                data=None,
                message=f"Service with ID {service_id} not found."
            )
        # Create and return a ResponseBO
        response = ResponseBO(
            code=200,  # HTTP status code for OK
            status="OK",
            data=result,
            message="Service retrieved successfully."
        )
        return response

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

# @subscription_router.put("/service/update/{service_id}", response_model=ResponseBO)
# async def update_service(service_id: int, data: CreateService):
#     worker_id = str(uuid.uuid4())  # Generate a unique worker_id
#     logger = setup_logger(worker_id)  # Set up logging with the worker_id
#
#     try:
#         logger.info(f"Received request to update service ID {service_id} with data: {data}")
#
#         # Check if the service name already exists for another service
#         existing_service = await subscription_service.check_update_service_name_exists(data.name, service_id, logger)
#         if existing_service:
#             # raise HTTPException(status_code=409, detail="Service name already exists for another service")
#             return ResponseBO(
#                 code=409,
#                 status="CONFLICT",
#                 data=None,
#                 message=f"Service name: '{data.name}' already exists for another service"
#             )
#
#         result = await subscription_service.update_service(service_id, data, logger)
#
#         if not result:
#             raise HTTPException(status_code=404, detail="Failed to update service")
#
#         # Create and return a ResponseBO
#         response = ResponseBO(
#             code=200,  # HTTP status code for OK
#             status="success",
#             data=result,
#             message="Service updated successfully."
#         )
#         return response
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

@subscription_router.put("/service/update/{service_id}", response_model=ResponseBO)
async def update_service(service_id: int, data: CreateService):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request to update service ID {service_id} with data: {data}")

        # Check if the service exists
        service = await subscription_service.get_service_by_id(service_id, logger)
        if not service:
            logger.error(f"Service with ID {service_id} not found.")
            # raise HTTPException(
            #     status_code=404,
            #     detail=f"Service with ID {service_id} not found."
            # )
            return ResponseBO(
                code=404,
                status="NOT FOUND",
                data=None,
                message=f"Service with ID {service_id} not found."
            )

        # Check if the new service name already exists for another service
        existing_service = await subscription_service.check_update_service_name_exists(data.name, service_id, logger)
        if existing_service:
            logger.error(f"Service name '{data.name}' already exists for another service.")
            # raise HTTPException(
            #     status_code=409,
            #     detail=f"Service name '{data.name}' already exists for another service."
            # )
            return ResponseBO(
                   code=409,
                   status="CONFLICT",
                   data=None,
                   message=f"Service name: '{data.name}' already exists for another service"
            )

        # Validate subscription_id
        logger.info(f"Validating subscription ID: {data.subscription_id}")
        subscription = await subscription_service.get_subscription_by_id(data.subscription_id, logger)
        if not subscription:
            logger.error(f"Subscription ID {data.subscription_id} not found.")
            # raise HTTPException(
            #     status_code=404,
            #     detail=f"Subscription with ID {data.subscription_id} not found."
            # )
            return ResponseBO(
                code=404,
                status="NOT FOUND",
                data=None,
                message=f"Subscription with ID {data.subscription_id} not found."
            )


        # Validate api_permission_id list
        if data.api_permission_id:
            logger.info(f"Validating API permission IDs: {data.api_permission_id}")
            invalid_permissions = await subscription_service.validate_api_permissions(data.api_permission_id, logger)
            if invalid_permissions:
                logger.error(f"Invalid API permission IDs: {invalid_permissions}")
                # raise HTTPException(
                #     status_code=404,
                #     detail=f"Invalid API permission IDs: {invalid_permissions}"
                # )
                return ResponseBO(
                    code=404,
                    status="NOT FOUND",
                    data=None,
                    message=f"Invalid API permission IDs: {invalid_permissions}."
                )

        # Update the service
        result = await subscription_service.update_service(service_id, data, logger)
        if not result:
            # raise HTTPException(
            #     status_code=404,
            #     detail="Failed to update service."
            # )
            return ResponseBO(
                code=404,
                status="NOT FOUND",
                data=None,
                message="Failed to create service."
            )

        # Create and return a ResponseBO
        response = ResponseBO(
            code=200,
            status="UPDATED",
            data=result,
            message="Service updated successfully."
        )
        return response

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


@subscription_router.get("/service/getAll", response_model=ResponseBO)
async def get_all_services():
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info("Received request to get all services")
        results = await subscription_service.get_all_services(logger)
        if not results:
            return ResponseBO(
                code=204,  # HTTP status code for OK
                status="NO CONTENT",
                data=results,
                message="No services found"
            )
        # Create and return a ResponseBO
        response = ResponseBO(
            code=200,  # HTTP status code for OK
            status="LIST RETRIEVED",
            data=results,
            message=f"{len(results)} Services retrieved successfully."
        )
        return response

    except asyncpg.PostgresError as pg_exc:
        logger.error(f"Database error occurred: {pg_exc}")
        raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")


@subscription_router.delete("/service/delete/serviceId/{service_id}/subscriptionId/{subscription_id}", response_model=ResponseBO)
async def handle_delete_service(service_id: int, subscription_id: int):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request to delete service ID {service_id} from subscription ID {subscription_id}")
        await subscription_service.delete_service_by_id(service_id, subscription_id, logger)
        if not subscription_id:
            return ResponseBO(
                code=404,
                status="NOT FOUND",
                data=None,
                message=f"Subscription with ID {subscription_id} not found."
            )
        if not service_id:
            return ResponseBO(
                code=404,
                status="NOT FOUND",
                data=None,
                message=f"Service with ID {service_id} not found."
            )
        # Create and return a ResponseBO
        response = ResponseBO(
            code=200,  # HTTP status code for OK
            status="DELETED",
            data=None,
            message="Service deleted successfully from subscription."
        )
        return response

    except HTTPException as http_exc:
        logger.error(f"HTTPException occurred: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")


@subscription_router.get("/service/getBySubscriptionId/{subscription_id}", response_model=ResponseBO)
async def get_services_by_subscription(subscription_id: int):
    worker_id = str(uuid.uuid4())
    logger = setup_logger(worker_id)

    try:
        logger.info(f"Received request to get services for subscription ID {subscription_id}")

        # Fetch services by subscription ID using the service function
        result = await subscription_service.get_services_by_subscription_id(subscription_id, logger)
        if not result:
            return ResponseBO(
                code=404,
                status="NOT FOUND",
                data=None,
                message=f"No services found for subscription ID {subscription_id}."
            )
        # if not subscription_id:
        #     return ResponseBO(
        #         code=404,
        #         status="NOT FOUND",
        #         data=None,
        #         message=f"Subscription with ID {subscription_id} not found."
        #     )
        response = ResponseBO(
            code=200,
            status="success",
            data=result,
            message=f"{len(result)} Services retrieved successfully."
        )
        return response

    except HTTPException as http_exc:
        logger.error(f"HTTPException occurred: {http_exc.detail}")
        raise http_exc
    #
    # except asyncpg.PostgresError as pg_exc:
    #     logger.error(f"Database error occurred: {pg_exc}")
    #     raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
    #
    # except Exception as e:
    #     logger.error(f"An unexpected error occurred: {e}")
    #     raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later." +" "+str(e))


@subscription_router.post("/service/servicesMapping", response_model=ResponseBO)
async def create_subscription_service_mapping(data: CreateSubscriptionServiceMapping):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request with data: {data}")

        # Check if the subscription exists
        existing_subscription = await subscription_service.check_subscription_exists(data.subscription_id, logger)
        if not existing_subscription:
            # raise HTTPException(status_code=404, detail="Subscription not found")
            return ResponseBO(
                code=404,
                status="NOT FOUND",
                data=None,
                message=f"Subscription with ID {data.subscription_id} not found."
            )

        # Check if all services exist
        existing_services = await subscription_service.check_services_exist(data.service_id, logger)
        if not existing_services:
            # raise HTTPException(status_code=409, detail="One or more service IDs do not exist")
            return ResponseBO(
                code=404,
                status="NOT FOUND",
                data=None,
                message=f"Service with ID {data.service_id} not found."
            )
        # Create service mapping and retrieve the updated subscription as DTO
        response = await subscription_service.create_service_mapping(data.subscription_id, data.service_id, logger)

        return response

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


@subscription_router.post("/service/apiPermissions/create", response_model=ResponseBO)
async def create_api_permission(data: CreateApiPermission):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request with data: {data}")

        # Check if the API permission name already exists
        existing_permission = await subscription_service.check_api_permission_name_exists(data.name, logger)
        if existing_permission:
            # raise HTTPException(status_code=409, detail="API permission name already exists")
            return ResponseBO(
                code=409,
                status="CONFLICT",
                data=None,
                message=f"Api_Permission name: '{data.name}' already exists for another api_permission"
            )

        result = await subscription_service.create_api_permission(data, logger)

        if not result:
            raise HTTPException(status_code=404, detail="Failed to create API permission")

        # Create and return a ResponseBO
        response = ResponseBO(
            code=201,  # HTTP status code for Created
            status="CREATED",
            data=result,
            message="API permission created successfully."
        )
        return response

    except HTTPException as http_exc:
        logger.error(f"HTTPException occurred: {http_exc.detail}")
        raise http_exc
    except ValueError as ve:
        logger.error(f"ValueError occurred: {ve}")
        raise HTTPException(status_code=400, detail=f"Value error: {ve}")
    except SQLAlchemyError as e:
        logger.error(f"Database error occurred: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")


@subscription_router.put("/service/apiPermissions/update/{api_permission_id}", response_model=ResponseBO)
async def update_api_permission(api_permission_id: int, data: CreateApiPermission):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request to update API permission ID {api_permission_id} with data: {data}")

        # Check if the API permission name already exists for another permission
        existing_permission = await subscription_service.check_update_api_permission_name_exists(data.name, api_permission_id, logger)
        if existing_permission:
            # raise HTTPException(status_code=409, detail="API permission name already exists for another permission")
            return ResponseBO(
                code=409,
                status="CONFLICT",
                data=None,
                message=f"Api_Permission name: '{data.name}' already exists for another api_permission"
            )

        result = await subscription_service.update_api_permission(api_permission_id, data, logger)

        if not result:
            # raise HTTPException(status_code=404, detail="Failed to update API permission")
            return ResponseBO(
                code=404,
                status="NOT FOUND",
                data=None,
                message=f"Api_Permissions with ID {api_permission_id} not found."
            )

        # Create and return a ResponseBO
        response = ResponseBO(
            code=200,  # HTTP status code for OK
            status="UPDATED",
            data=result,
            message="API permission updated successfully."
        )
        return response

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


@subscription_router.get("/service/apiPermissions/getAll", response_model=ResponseBO)
async def get_all_api_permissions():
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info("Received request to get all API permissions")
        results = await subscription_service.get_all_api_permissions(logger)
        if not results:
            return ResponseBO(
                code=204,  # HTTP status code for OK
                status="NO CONTENT",
                data=results,
                message="No api_permissions found"
            )
        # Create and return a ResponseBO
        response = ResponseBO(
            code=200,  # HTTP status code for OK
            status="LIST RETRIEVED",
            data=results,
            message="API permissions retrieved successfully."
        )
        return response

    except asyncpg.PostgresError as pg_exc:
        logger.error(f"Database error occurred: {pg_exc}")
        raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")


@subscription_router.get("/service/apiPermissions/get/{api_permission_id}", response_model=ResponseBO)
async def get_api_permission(api_permission_id: int):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request to get API permission ID {api_permission_id}")
        result = await subscription_service.get_api_permission_by_id(api_permission_id, logger)

        # Check if the result is None, which means not found
        if not result:
            response = ResponseBO(
                code=404,  # HTTP status code for Not Found
                status="NOT FOUND",
                data=None,
                message=f"API permission with ID {api_permission_id} not found."
            )
            logger.warning(response.message)
            return response

        # Create and return a ResponseBO if found
        response = ResponseBO(
            code=200,  # HTTP status code for OK
            status="OK",
            data=result,
            message="API permission retrieved successfully."
        )
        return response

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


@subscription_router.delete("/service/apiPermissions/delete/{api_permission_id}", response_model=ResponseBO)
async def handle_delete_api_permission(api_permission_id: int):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request to delete API permission ID {api_permission_id}")
        api_permission = await subscription_service.delete_api_permission(api_permission_id, logger)
        if not api_permission:
            response = ResponseBO(
                code=404,  # HTTP status code for Not Found
                status="NOT FOUND",
                data=None,
                message=f"API permission with ID {api_permission_id} not found."
            )
            return response
        # Create and return a ResponseBO
        response = ResponseBO(
            code=200,  # HTTP status code for OK
            status="DELETED",
            data=None,
            message="API permission deleted successfully."
        )
        return response

    except HTTPException as http_exc:
        logger.error(f"HTTPException occurred: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")


@subscription_router.post("/service/apiPermissions/apiPermissionsMapping", response_model=ResponseBO)
async def create_service_api_permissions_mapping(data: CreateServiceApiPermissionMapping):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request with data: {data}")

        # Check if the service exists
        existing_service = await subscription_service.check_service_exists(data.service_id, logger)
        if not existing_service:
            # raise HTTPException(status_code=404, detail="Service not found")
            return ResponseBO(
                code=404,
                status="NOT FOUND",
                data=None,
                message=f"Service with ID {data.service_id} not found."
            )

        # Check if all API permissions exist
        existing_permissions = await subscription_service.check_permissions_exist(data.api_permission_id, logger)
        if not existing_permissions:
            # raise HTTPException(status_code=409, detail="One or more API permission IDs do not exist")
            return ResponseBO(
                code=404,
                status="NOT FOUND",
                data=None,
                message=f"Api_Permission_Id: '{data.api_permission_id}' not found"
            )

        # Create API permission mapping and retrieve the updated service as DTO
        response = await subscription_service.create_api_permissions_mapping(data.service_id, data.api_permission_id, logger)

        return response

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


@subscription_router.get("/service/apiPermissions/getApiPermissionsByServiceId/{service_id}", response_model=ResponseBO)
async def get_api_permissions_by_service(service_id: int):
    worker_id = str(uuid.uuid4())
    logger = setup_logger(worker_id)

    try:
        logger.info(f"Received request to get API permissions for service ID {service_id}")

        # Fetch API permissions by service ID using the service function
        result = await subscription_service.get_api_permissions_by_service_id(service_id, logger)
        if not result:
            return ResponseBO(
                code=404,
                status="NOT FOUND",
                data=None,
                message=f"Service with ID {service_id} not found."
            )

        # response = ResponseBO(
        #     code=200,
        #     status="OK",
        #     data=result,
        #     message=f"{len(result)} API permissions retrieved successfully."
        # )
        return result

    except HTTPException as http_exc:
        logger.error(f"HTTPException occurred: {http_exc.detail}")
        raise http_exc

    except asyncpg.PostgresError as pg_exc:
        logger.error(f"Database error occurred: {pg_exc}")
        raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later." + " " + str(e))




#Page Permissions



@subscription_router.post("/pagePermissions/create", response_model=ResponseBO, status_code=201)
async def create_permission(data: PagePermissionDTO):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        existing_permission = await subscription_service.check_update_page_permission_name_exists(data.name,data.id,logger)
        if existing_permission:
            return ResponseBO(
                code=409,
                status="CONFLICT",
                data=None,
                message=f"Page permission name: '{data.name}' already exists for another page permission."
            )

        logger.info("Received request to create a new page permission")
        result = await subscription_service.create_page_permission(data,logger)

        response = ResponseBO(
            code=201,  # HTTP status code for CREATED
            status="CREATED",
            data=result,
            message="Page permission created successfully."
        )
        return response

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")


@subscription_router.put("/pagePermissions/update/{page_permission_id}", response_model=ResponseBO)
async def update_permission(page_permission_id: int, data: PagePermissionCreateDTO):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request to update page permission ID {page_permission_id} with data: {data}")

        # Check if the page permission name already exists for another permission
        existing_permission = await subscription_service.check_update_page_permission_name_exists(data.name, page_permission_id, logger)
        if existing_permission:
            return ResponseBO(
                code=409,
                status="CONFLICT",
                data=None,
                message=f"Page permission name: '{data.name}' already exists for another page permission."
            )

        # Update the page permission
        result = await subscription_service.update_page_permission(page_permission_id, data, logger)

        if not result:
            return ResponseBO(
                code=404,
                status="NOT FOUND",
                data=None,
                message=f"Page Permission with ID {page_permission_id} not found."
            )

        # Create and return a ResponseBO
        response = ResponseBO(
            code=200,  # HTTP status code for OK
            status="UPDATED",
            data=result,
            message="Page permission updated successfully."
        )
        return response

    except HTTPException as http_exc:
        logger.error(f"HTTPException occurred: {http_exc.detail}")
        raise http_exc
    except ValueError as ve:
        logger.error(f"ValueError occurred: {ve}")
        raise HTTPException(status_code=400, detail=f"Value error: {ve}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")


@subscription_router.delete("/pagePermissions/delete/{permission_id}", response_model=ResponseBO)
async def delete_permission(permission_id: int):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request to delete page permission ID {permission_id}")

        # Delete the page permission
        response = await subscription_service.delete_page_permission(permission_id, logger)

        if response.code == 404:
            return response  # Return the 404 response directly

        # If deletion was successful, return the success response
        return response

    except HTTPException as http_exc:
        logger.error(f"HTTPException occurred: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")


@subscription_router.get("/pagePermissions/get/{page_permission_id}", response_model=ResponseBO)
async def get_page_permission(page_permission_id: int):
    worker_id = str(uuid.uuid4())
    logger = setup_logger(worker_id)

    try:
        logger.info(f"Received request to get page permission ID {page_permission_id}")
        result = await subscription_service.get_page_permission_by_id(page_permission_id, logger)
        if not result:
            return ResponseBO(
                code=404,
                status="NOT FOUND",
                data=None,
                message=f"Page Permission with ID {page_permission_id} not found."
            )
        response = ResponseBO(
            code=200,
            status="OK",
            data=result,
            message="Page Permission retrieved successfully."
        )
        return response

    except HTTPException as http_exc:
        logger.error(f"HTTPException occurred: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")

# FastAPI route for getAll
@subscription_router.get("/pagePermissions/getAll", response_model=ResponseBO)
async def get_all_page_permissions():
    worker_id = str(uuid.uuid4())
    logger = setup_logger(worker_id)

    try:
        logger.info("Received request to get all page permissions")
        results = await subscription_service.get_all_page_permissions(logger)
        if not results:
            return ResponseBO(
                code=204,
                status="NO CONTENT",
                data=results,
                message="No page permissions found"
            )
        response = ResponseBO(
            code=200,
            status="LIST RETRIEVED",
            data=results,
            message=f"{len(results)} Page Permissions retrieved successfully."
        )
        return response

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")

@subscription_router.post("/pagePermissions/pagePermissionsMapping", response_model=ResponseBO)
async def create_service_page_permissions_mapping(data: ServiceApiPagePermissionsMappingCreateDTO):
    worker_id = str(uuid.uuid4())  # Generate a unique worker_id
    logger = setup_logger(worker_id)  # Set up logging with the worker_id

    try:
        logger.info(f"Received request with data: {data}")

        # Check if the service exists
        existing_service = await subscription_service.check_service_exists(data.service_id, logger)
        if not existing_service:
            return ResponseBO(
                code=404,
                status="NOT FOUND",
                data=None,
                message=f"Service with ID {data.service_id} not found."
            )

        # Check if the page permissions exist
        existing_permissions = await subscription_service.check_page_permissions_exist(data.page_permission_id, logger)
        if not existing_permissions:
            return ResponseBO(
                code=404,
                status="NOT FOUND",
                data=None,
                message=f"One or more page permissions not found: {data.page_permission_id}"
            )

        # Create page permission mapping and retrieve the updated service as DTO
        response = await subscription_service.create_page_permissions_mapping(data.service_id, data.page_permission_id, logger)

        return response

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
