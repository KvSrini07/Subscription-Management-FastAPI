from typing import List, Optional, Union

import asyncpg
from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import SubscriptionEntity, SubscriptionType, ServiceEntity, SubscriptionServicesMapping, \
    ApiPermissionEntity, ServiceApiPermissionsMapping, PagePermissionEntity, ServiceApiPagePermissionsMapping
from app.models.pydantic_models import CreateSubscription, SubscriptionDTO, ServiceDTO, ApiPermissionDTO, CreateService, \
    CreateApiPermission, PagePermissionDTO, PagePermissionCreateDTO
import logging
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.configuration.db import ConnectionManager
from fastapi import HTTPException

from app.models.response import ResponseBO


async def check_subscription_name_exists(name: str, logger: logging.Logger) -> bool:
    async with ConnectionManager() as session:  # Assuming ConnectionManager manages your async session
        try:
            # Query the SubscriptionEntity to check for existing subscription name
            result = await session.execute(
                select(SubscriptionEntity).filter_by(name=name)
            )
            # Check if any subscription with the given name exists
            return result.scalars().first() is not None
        except SQLAlchemyError as e:
            logger.error(f"Database error while checking subscription name: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred.")

async def check_service_name_exists(name: str, logger: logging.Logger) -> bool:
    async with ConnectionManager() as session:
        try:
            existing_service = await session.execute(
                select(ServiceEntity).filter_by(name=name)
            )
            return existing_service.scalars().first() is not None
        except SQLAlchemyError as e:
            logger.error(f"Database error while checking service name: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred.")

async def check_update_subscription_name_exists(name: str, exclude_id: int, logger: logging.Logger) -> bool:
    async with ConnectionManager() as session:
        try:
            existing_subscription = await session.execute(
                select(SubscriptionEntity).filter(SubscriptionEntity.name == name, SubscriptionEntity.id != exclude_id)
            )
            return existing_subscription.scalars().first() is not None
        except SQLAlchemyError as e:
            logger.error(f"Database error while checking subscription name: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred.")


async def fetch_subscription_with_relationships(subscription_id: int, session, logger) -> SubscriptionEntity:
    logger.info(f"Fetching subscription with ID: {subscription_id}")

    try:
        # Fetch the subscription by ID with eager loading of related entities
        result = await session.execute(
            select(SubscriptionEntity)
            .options(
                selectinload(SubscriptionEntity.services)  # Eager load the services relationship
                .selectinload(ServiceEntity.api_permissions),  # Eager load related ApiPermissionEntity
                selectinload(SubscriptionEntity.services)
                .selectinload(ServiceEntity.page_permissions)
            )
            .filter(SubscriptionEntity.id == subscription_id)
        )

        subscription = result.scalars().first()

        if subscription:
            logger.info(f"Successfully retrieved subscription: {subscription}")
        else:
            logger.warning(f"Subscription with ID {subscription_id} not found.")

        return subscription

    except Exception as e:
        logger.error(f"Error occurred while fetching subscription with ID {subscription_id}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching the subscription.")




async def create_subscription(data: CreateSubscription, logger: logging.Logger):
    async with ConnectionManager() as session:
        try:
            new_subscription = dto_to_entity(data, logger)  # Convert DTO to entity
            session.add(new_subscription)
            await session.commit()
            subscription = await fetch_subscription_with_relationships(new_subscription.id, session, logger)
            logger.info(f"Subscription created: {new_subscription}")
            return entity_to_dto(subscription, logger)  # Convert entity to DTO
        except SQLAlchemyError as e:
            logger.error(f"Failed to create subscription: {e}")
            await session.rollback()
            raise

async def update_subscription(subscription_id: int, data: CreateSubscription, logger: logging.Logger):
    async with ConnectionManager() as session:
        try:
            # Fetch the existing subscription
            existing_subscription = await fetch_subscription_with_relationships(subscription_id, session, logger)
            if not existing_subscription:
                logger.error(f"Subscription with ID {subscription_id} not found.")
                # raise HTTPException(status_code=404, detail="Subscription not found")
                return None

            existing_subscription.name = data.name
            existing_subscription.validity = data.validity
            existing_subscription.cost = data.cost
            existing_subscription.active_status = data.active_status
            existing_subscription.subscription_type = SubscriptionType[data.subscription_type]

            session.add(existing_subscription)
            await session.commit()
            logger.info(f"Subscription updated: {existing_subscription}")
            return entity_to_dto(existing_subscription, logger)  # Return the updated entity or convert to DTO if needed

        except SQLAlchemyError as e:
            logger.error(f"Failed to update subscription: {e}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
        except Exception as e:
            logger.error(f"An unexpected error occurred while updating: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")


# async def get_subscription_by_id(subscription_id: int, logger: logging.Logger):
#     async with ConnectionManager() as session:
#         try:
#             # Fetch the subscription by ID
#             subscription = await fetch_subscription_with_relationships(subscription_id, session, logger)
#             if not subscription:
#                 logger.error(f"Subscription with ID {subscription_id} not found.")
#                 raise HTTPException(status_code=404, detail="Subscription not found")
#             logger.info(f"Retrieved subscription: {subscription}")
#             return entity_to_dto(subscription, logger)   # Return the entity or convert to DTO if needed
#
#         except SQLAlchemyError as e:
#             logger.error(f"Database error occurred while fetching subscription: {e}")
#             raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
#         except Exception as e:
#             logger.error(f"An unexpected error occurred while fetching subscription: {e}")
#             raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")

#After add responseBO
async def get_subscription_by_id(subscription_id: int, logger: logging.Logger):
    async with ConnectionManager() as session:
        try:
            # Fetch the subscription by ID
            subscription = await fetch_subscription_with_relationships(subscription_id, session, logger)

            if not subscription:
                logger.error(f"Subscription with ID {subscription_id} not found.")
                # Return None to let the router handle the 404 error
                return None

            logger.info(f"Retrieved subscription: {subscription}")
            # Convert entity to DTO if needed
            return entity_to_dto(subscription, logger)

        except SQLAlchemyError as e:
            logger.error(f"Database error occurred while fetching subscription: {e}")
            # Return a custom object indicating a database error
            return {"error": "db_error", "message": "Database error occurred. Please try again later."}

        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching subscription: {e}")
            # Return a generic error response to handle at the router level
            return {"error": "unexpected", "message": "An unexpected error occurred. Please try again later."}


async def get_all_subscriptions(logger: logging.Logger):
    async with ConnectionManager() as session:
        try:
            # Fetch all subscriptions from the database with eager loading
            result = await session.execute(
                select(SubscriptionEntity)
                .options(
                    selectinload(SubscriptionEntity.services)
                    .selectinload(ServiceEntity.api_permissions),
                    selectinload(SubscriptionEntity.services)
                    .selectinload(ServiceEntity.page_permissions)
                )
            )
            subscriptions = result.scalars().all()  # Fetch all results

            if not subscriptions:
                logger.warning("No subscriptions found.")
                return []  # Return an empty list if no subscriptions are found

            logger.info(f"Retrieved {len(subscriptions)} subscriptions.")
            return [entity_to_dto(subscription, logger) for subscription in subscriptions]

        except SQLAlchemyError as e:
            logger.error(f"Database error occurred while fetching subscriptions: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching subscriptions: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")

async def get_active_subscriptions(logger: logging.Logger):
    async with ConnectionManager() as session:
        try:
            # Fetch first 3 active subscriptions from the database
            result = await session.execute(
                select(SubscriptionEntity)
                .where(SubscriptionEntity.active_status == True)  # Filter by active status
                .limit(3)  # Fetch only the first 3 subscriptions
                .options(
                    selectinload(SubscriptionEntity.services)  # Eager load related services
                    # .selectinload(SubscriptionServicesMapping.service_id)
                    .selectinload(ServiceEntity.api_permissions),  # Eager load related ApiPermissionEntity
                    selectinload(SubscriptionEntity.services)
                    .selectinload(ServiceEntity.page_permissions)
                )
            )
            subscriptions = result.scalars().all()  # Fetch all results

            if not subscriptions:
                logger.warning("No active subscriptions found.")
                return []  # Return an empty list if no active subscriptions are found

            logger.info(f"Retrieved {len(subscriptions)} active subscriptions.")
            return [entity_to_dto(subscription, logger) for subscription in subscriptions]

        except SQLAlchemyError as e:
            logger.error(f"Database error occurred while fetching active subscriptions: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching active subscriptions: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")

async def delete_subscription(subscription_id: int, logger: logging.Logger):
    async with ConnectionManager() as session:
        try:
            # Fetch the subscription by ID to ensure it exists
            subscription = await fetch_subscription_with_relationships(subscription_id, session, logger)
            if not subscription:
                logger.error(f"Subscription with ID {subscription_id} not found for deletion.")
                # raise HTTPException(status_code=404, detail="Subscription not found.")
                return False

            # Proceed to delete the subscription
            await session.delete(subscription)
            await session.commit()  # Commit the transaction

            logger.info(f"Successfully deleted subscription with ID {subscription_id}.")
            return True

        except asyncpg.PostgresError as pg_exc:
            logger.error(f"Database error occurred while deleting subscription: {pg_exc}")
            raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
        except Exception as e:
            logger.error(f"An unexpected error occurred while deleting subscription: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")


def dto_to_entity(dto: CreateSubscription, logger: logging.Logger) -> SubscriptionEntity:
    logger.debug(f"Converting DTO to entity: {dto}")
    entity = SubscriptionEntity(
        name=dto.name,
        validity=dto.validity,
        cost=dto.cost,
        active_status=dto.active_status,
        subscription_type=SubscriptionType[dto.subscription_type]  # Convert string to enum
    )
    logger.info(f"Converted DTO to entity: {entity}")
    return entity


# def entity_to_dto(entity: SubscriptionEntity, logger: logging.Logger) -> SubscriptionDTO:
#     logger.debug(f"Converting entity to DTO: {entity}")
#
#     # Convert the related ServiceEntity instances to ServiceDTO
#     services = [
#         ServiceDTO(
#             id=service.id,  # Accessing service directly from ServiceEntity
#             name=service.name,
#             description=service.description,
#             active_status=service.active_status,
#             api_permissions=[
#                 ApiPermissionDTO(
#                     id=permission.id,  # Accessing api_permission directly from ApiPermissionEntity
#                     name=permission.name,
#                     method=permission.method.name if permission.method else None,  # Convert Enum to string
#                     api_url=permission.api_url,
#                     description=permission.description,
#                     status=permission.status
#                 )
#                 for permission in service.api_permissions if permission is not None  # Direct access to api_permissions
#             ]
#         )
#         for service in entity.services if service is not None  # Direct access to services in SubscriptionEntity
#     ] if entity.services is not None else []
#
#     dto = SubscriptionDTO(
#         id=entity.id,
#         name=entity.name,
#         validity=entity.validity,
#         cost=entity.cost,
#         active_status=entity.active_status,
#         subscription_type=entity.subscription_type.name if entity.subscription_type else None,  # Convert Enum to string
#         services=services
#     )
#
#     logger.info(f"Converted entity to DTO: {dto}")
#     return dto

def entity_to_dto(entity: SubscriptionEntity, logger: logging.Logger) -> SubscriptionDTO:
    logger.debug(f"Converting entity to DTO: {entity}")

    # Convert the related ServiceEntity instances to ServiceDTO
    services = [
        ServiceDTO(
            id=service.id,
            name=service.name,
            description=service.description,
            active_status=service.active_status,
            api_permissions=[
                ApiPermissionDTO(
                    id=permission.id,
                    name=permission.name,
                    method=permission.method.name if permission.method else None,  # Convert Enum to string
                    api_url=permission.api_url,
                    description=permission.description,
                    status=permission.status
                )
                for permission in service.api_permissions  # Direct access, no None check needed
            ],
            page_permissions=[
                PagePermissionDTO(
                    id=page_permission.id,
                    name=page_permission.name,
                    description=page_permission.description,
                    status=page_permission.status,
                    page_url=page_permission.page_url
                )
                for page_permission in service.page_permissions  # Direct access, no None check needed
            ]
        )
        for service in entity.services  # Direct access, no None check needed
    ]

    dto = SubscriptionDTO(
        id=entity.id,
        name=entity.name,
        validity=entity.validity,
        cost=entity.cost,
        active_status=entity.active_status,
        subscription_type=entity.subscription_type.name if entity.subscription_type else None,  # Convert Enum to string
        services=services
    )

    logger.info(f"Converted entity to DTO: {dto}")
    return dto




async def check_update_service_name_exists(name: str, exclude_id: int, logger: logging.Logger) -> bool:
    async with ConnectionManager() as session:
        try:
            existing_service = await session.execute(
                select(ServiceEntity).filter(ServiceEntity.name == name, ServiceEntity.id != exclude_id)
            )
            return existing_service.scalars().first() is not None
        except SQLAlchemyError as e:
            logger.error(f"Database error while checking service name: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred.")

async def fetch_service_with_relationships(service_id: int, session, logger) -> ServiceEntity:
    logger.info(f"Fetching service with ID: {service_id}")

    try:
        # Fetch the service by ID with eager loading of related entities
        result = await session.execute(
            select(ServiceEntity)
            .options(
                selectinload(ServiceEntity.subscriptions),  # Eager load the subscriptions relationship
                selectinload(ServiceEntity.api_permissions),
                selectinload(ServiceEntity.page_permissions)# Eager load related ApiPermissionEntity
            )
            .filter(ServiceEntity.id == service_id)
        )

        service = result.scalars().first()

        if service:
            logger.info(f"Successfully retrieved service: {service}")
        else:
            logger.warning(f"Service with ID {service_id} not found.")

        return service

    except Exception as e:
        logger.error(f"Error occurred while fetching service with ID {service_id}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching the service.")

async def check_subscription_exists(subscription_id: int, logger: logging.Logger):
    async with ConnectionManager() as session:
        result = await session.execute(select(SubscriptionEntity).filter_by(id=subscription_id))
        return result.scalars().first() is not None

async def check_services_exist(service_ids: List[int], logger: logging.Logger):
    async with ConnectionManager() as session:
        result = await session.execute(select(ServiceEntity).filter(ServiceEntity.id.in_(service_ids)))
        return len(result.scalars().all()) == len(service_ids)

async def validate_api_permissions(api_permission_ids: Optional[List[int]], logger: logging.Logger) -> List[
        int]:
        if not api_permission_ids:
            return []  # No IDs to validate

        async with ConnectionManager() as session:
            # Check which IDs are invalid
            invalid_ids = []
            for perm_id in api_permission_ids:
                permission = await session.get(ApiPermissionEntity, perm_id)
                if not permission:
                    invalid_ids.append(perm_id)
                    logger.error(f"API permission with ID {perm_id} not found.")

            return invalid_ids
async def fetch_delete_service_with_relationships(service_id: int, logger: logging.Logger):
    """Fetch the service along with related API permissions and subscriptions."""
    async with ConnectionManager() as session:
        logger.info(f"Fetching service with ID: {service_id}")
        result = await session.execute(
            select(ServiceEntity).filter(ServiceEntity.id == service_id)
        )
        service = result.scalars().first()

        if service:
            logger.info(f"Service {service_id} found.")
        else:
            logger.warning(f"Service with ID {service_id} not found.")

        return service



async def create_service(data: CreateService, logger: logging.Logger):
    async with ConnectionManager() as session:
        try:
            # Convert DTO to ServiceEntity
            new_service = await dto_to_service_entity(data, session, logger)

            # Add the new service entity to the session
            session.add(new_service)
            logger.info(f"New service entity added to session: {new_service}")

            await session.commit()

            # Fetch the subscription entity using subscription_id from the DTO
            if data.subscription_id:
                logger.info(f"Fetching subscription with ID: {data.subscription_id}")

                result = await session.execute(
                    select(SubscriptionEntity).filter(SubscriptionEntity.id == data.subscription_id)
                )
                subscription = result.scalars().first()

                if subscription is not None:
                    # Associate the subscription with the new service
                    subscription_mapping = SubscriptionServicesMapping(
                        subscription_id=subscription.id,
                        service_id=new_service.id
                    )
                    session.add(subscription_mapping)
                    logger.info(f"Associated subscription ID {data.subscription_id} with the service.")
                else:
                    logger.warning(f"No subscription found with ID: {data.subscription_id}")

            await session.commit()

            # If api_permission_id is provided, check for existing mappings
            if data.api_permission_id is not None:  # Check if api_permission_id is not None
                logger.info(f"Checking existing API permissions for service ID: {new_service.id}")

                existing_permissions_query = await session.execute(
                    select(ServiceApiPermissionsMapping.api_permission_id).where(
                        ServiceApiPermissionsMapping.service_id == new_service.id,
                        ServiceApiPermissionsMapping.api_permission_id.in_(data.api_permission_id)
                    )
                )
                existing_permissions_ids = {perm_id for perm_id in existing_permissions_query.scalars()}

                # Add only those API permissions that are not already mapped
                for api_permission_id in data.api_permission_id:
                    if api_permission_id not in existing_permissions_ids:
                        api_permission_mapping = ServiceApiPermissionsMapping(
                            service_id=new_service.id,
                            api_permission_id=api_permission_id
                        )
                        session.add(api_permission_mapping)
                        logger.info(f"Added API permission ID {api_permission_id} to service ID {new_service.id}.")
                    else:
                        logger.info(f"API permission ID {api_permission_id} already exists for service ID {new_service.id}, skipping.")

            # Commit the transaction
            await session.commit()
            logger.info(f"Service created: {new_service}")

            service = await fetch_service_with_relationships(new_service.id, session, logger)

            return entity_to_service_dto(service, logger)  # Convert entity to DTO

        except SQLAlchemyError as e:
            logger.error(f"Failed to create service: {e}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred.")

async def update_service(service_id: int, data: CreateService, logger: logging.Logger):
    async with ConnectionManager() as session:
        try:
            # Fetch the existing service
            existing_service = await fetch_service_with_relationships(service_id, session, logger)
            if not existing_service:
                logger.error(f"Service with ID {service_id} not found.")
                raise HTTPException(status_code=404, detail="Service not found")

            # Update service fields
            if data.name is not None:
                existing_service.name = data.name
            if data.description is not None:
                existing_service.description = data.description
            if data.active_status is not None:
                existing_service.active_status = data.active_status

            # Update API permissions if provided
            if data.api_permission_id:
                # Clear existing permissions if needed, then add the new ones
                existing_service.api_permissions.clear()  # Clear existing relationships

                api_permissions_query = await session.execute(
                    select(ApiPermissionEntity).where(
                        ApiPermissionEntity.id.in_(data.api_permission_id)
                    )
                )
                api_permissions = api_permissions_query.scalars().all()

                for api_permission in api_permissions:
                    existing_service.api_permissions.append(api_permission)

            # If a subscription ID is provided, handle that logic
            if data.subscription_id:
                subscription_mapping = SubscriptionServicesMapping(
                    subscription_id=data.subscription_id,
                    service_id=existing_service.id
                )
                session.add(subscription_mapping)
                logger.info(f"Associated subscription ID {data.subscription_id} with the service.")

            # Commit the changes
            await session.commit()
            logger.info(f"Service updated: {existing_service}")
            return entity_to_service_dto(existing_service, logger)  # Return the updated entity as DTO

        except SQLAlchemyError as e:
            logger.error(f"Failed to update service: {e}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
        except Exception as e:
            logger.error(f"An unexpected error occurred while updating: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")


async def get_service_by_id(service_id: int, logger: logging.Logger):
    async with ConnectionManager() as session:
        try:
            # Fetch the service by ID
            service = await fetch_service_with_relationships(service_id, session, logger)
            if not service:
                logger.error(f"Service with ID {service_id} not found.")
                raise HTTPException(status_code=404, detail="Service not found")
            logger.info(f"Retrieved service: {service}")
            return entity_to_service_dto(service, logger)  # Convert to DTO if needed

        except SQLAlchemyError as e:
            logger.error(f"Database error occurred while fetching service: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching service: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")


async def get_all_services(logger: logging.Logger):
    async with ConnectionManager() as session:
        try:
            # Fetch all services from the database with eager loading
            result = await session.execute(
                select(ServiceEntity)
                .options(
                    selectinload(ServiceEntity.api_permissions),  # Eager load related API permissions
                    selectinload(ServiceEntity.page_permissions)
                )
            )
            services = result.scalars().all()  # Fetch all results

            if not services:
                logger.warning("No services found.")
                return []  # Return an empty list if no services are found

            logger.info(f"Retrieved {len(services)} services.")
            return [entity_to_service_dto(service, logger) for service in services]

        except SQLAlchemyError as e:
            logger.error(f"Database error occurred while fetching services: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching services: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")

async def get_services_by_subscription_id(subscription_id: int, logger: logging.Logger) -> Optional[List[ServiceDTO]]:
    async with ConnectionManager() as session:
        try:
            # Fetch the subscription entity with related services
            subscription = await fetch_subscription_with_relationships(subscription_id, session, logger)

            if not subscription:
                logger.error(f"Subscription with ID {subscription_id} not found.")
                # raise HTTPException(status_code=404, detail="Subscription not found")
                return None

            # Convert the services to DTOs
            service_dtos = [
                entity_to_service_dto(service, logger) for service in subscription.services
            ]

            if not service_dtos:
                logger.warning(f"No services found for subscription ID {subscription_id}.")
                # raise HTTPException(status_code=404, detail="No services found for the subscription")
                return None

            logger.info(f"Successfully retrieved {len(service_dtos)} services for subscription ID {subscription_id}")
            return service_dtos

        except SQLAlchemyError as e:
            logger.error(f"Database error occurred: {e}")
            raise HTTPException(status_code=500, detail="Database error. Please try again later.")
        # except Exception as e:
        #     logger.error(f"An unexpected error occurred: {e}")
        #     raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")

async def create_service_mapping(subscription_id: int, service_ids: List[int], logger: logging.Logger):
    async with ConnectionManager() as session:
        # Retrieve existing mappings for the given subscription_id
        existing_mappings = await session.execute(
            select(SubscriptionServicesMapping).where(SubscriptionServicesMapping.subscription_id == subscription_id)
        )
        existing_service_ids = {mapping.service_id for mapping in existing_mappings.scalars().all()}

        # Filter service_ids to include only those not already mapped
        new_service_ids = [service_id for service_id in service_ids if service_id not in existing_service_ids]

        # Create mappings for the new service IDs
        for service_id in new_service_ids:
            mapping = SubscriptionServicesMapping(subscription_id=subscription_id, service_id=service_id)
            session.add(mapping)

        await session.commit()
        logger.info(f"Services mapped to subscription {subscription_id}: {service_ids}")

        # Fetch the updated subscription from the database
        updated_subscription = await fetch_subscription_with_relationships(subscription_id, session, logger)

        # Convert the updated subscription entity to DTO
        subscription_dto = entity_to_dto(updated_subscription, logger)

        # Construct and return the ResponseBO
        return ResponseBO(
            code=201,  # HTTP status code for Created
            status="success",
            data=subscription_dto,
            message="Service mapping created successfully."
        )

async def delete_service_by_id(service_id: int, subscription_id: int, logger: logging.Logger):
    """Deletes a service by ID along with related mappings."""
    async with ConnectionManager() as session:
        # Fetch the service entity
        service = await fetch_delete_service_with_relationships(service_id, logger)
        if not service:
            raise HTTPException(
                status_code=404,
                detail=f"Service ID {service_id} not found."
            )

        # Verify if the subscription exists
        subscription = await session.get(SubscriptionEntity, subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=404,
                detail=f"Subscription ID {subscription_id} not found."
            )

        # Check if API permission mappings exist for the service
        api_permission_mappings = await session.execute(
            select(ServiceApiPermissionsMapping)
            .where(ServiceApiPermissionsMapping.service_id == service_id)
        )
        if not api_permission_mappings.scalars().all():
            logger.warning(f"No API permission mappings found for service ID {service_id}.")

        # Delete API permission mappings
        await session.execute(
            delete(ServiceApiPermissionsMapping)
            .where(ServiceApiPermissionsMapping.service_id == service_id)
        )

        page_permission_mappings = await session.execute(
            select(ServiceApiPagePermissionsMapping)
            .where(ServiceApiPagePermissionsMapping.service_id == service_id)
        )
        if not page_permission_mappings.scalars().all():
            logger.warning(f"No Page permission mappings found for service ID {service_id}.")

        # Delete page permission mappings
        await session.execute(
            delete(ServiceApiPagePermissionsMapping)
            .where(ServiceApiPagePermissionsMapping.service_id == service_id)
        )

        # Check if the service is linked with the subscription
        subscription_mapping = await session.execute(
            select(SubscriptionServicesMapping)
            .where(
                SubscriptionServicesMapping.subscription_id == subscription_id,
                SubscriptionServicesMapping.service_id == service_id
            )
        )
        if not subscription_mapping.scalars().first():
            raise HTTPException(
                status_code=404,
                detail=f"No mapping found between subscription {subscription_id} and service {service_id}."
            )

        # Delete subscription-service mappings
        await session.execute(
            delete(SubscriptionServicesMapping)
            .where(
                SubscriptionServicesMapping.subscription_id == subscription_id,
                SubscriptionServicesMapping.service_id == service_id
            )
        )

        # Delete the service entity
        await session.delete(service)
        await session.commit()

        logger.info(f"Successfully deleted service with ID {service_id}.")
        return {"status": "success", "message": f"Service with ID {service_id} deleted successfully."}

async def dto_to_service_entity(service_dto: CreateService, session: AsyncSession, logger: logging.Logger) -> ServiceEntity:
    logger.info(f"Mapping CreateService DTO to ServiceEntity: {service_dto}")

    # Create ServiceEntity from the DTO
    service_entity = ServiceEntity(
        name=service_dto.name,
        description=service_dto.description,
        active_status=service_dto.active_status
    )

    # If api_permission_id is provided, map them to the entity
    if service_dto.api_permission_id:
        logger.info(f"Mapping API permissions with IDs: {service_dto.api_permission_id}")

        # Fetch the API Permission Entities from the database based on provided IDs
        api_permissions_query = await session.execute(
            select(ApiPermissionEntity).where(
                ApiPermissionEntity.id.in_(service_dto.api_permission_id)
            )
        )

        api_permissions = api_permissions_query.scalars().all()

        # Associate the fetched ApiPermissionEntities with the ServiceEntity
        service_entity.api_permissions = api_permissions

    return service_entity

def entity_to_service_dto(service_entity: ServiceEntity, logger: logging.Logger) -> ServiceDTO:
    logger.info(f"Mapping ServiceEntity to ServiceDTO: {service_entity}")

    # Map API permissions if they exist
    api_permissions_dto = [
        ApiPermissionDTO(
            id=perm.id,  # Directly access the id attribute
            name=perm.name,
            method=perm.method,
            api_url=perm.api_url,
            description=perm.description,
            status=perm.status
        )
        for perm in service_entity.api_permissions  # Use the correct relationship
    ] if service_entity.api_permissions else []

    page_permissions_dto = [
        PagePermissionDTO.from_orm(permission)  # Use ORM model conversion
        for permission in service_entity.page_permissions  # Correct relationship for Page permissions
    ] if service_entity.page_permissions else []

    # page_permissions_dto = [
    #     PagePermissionDTO(
    #         id=perm.id,  # Directly access the id attribute
    #         name=perm.name,
    #         page_url=perm.page_url,
    #         description=perm.description,
    #         status=perm.status
    #     )
    #     for perm in service_entity.page_permissions  # Use the correct relationship
    # ] if service_entity.page_permissions else []

    # Create ServiceDTO from the ServiceEntity
    service_dto = ServiceDTO(
        id=service_entity.id,
        name=service_entity.name,
        description=service_entity.description,
        active_status=service_entity.active_status,
        api_permissions=api_permissions_dto,
        page_permissions = page_permissions_dto
    )

    logger.info(f"Mapped ServiceEntity to ServiceDTO with {len(api_permissions_dto)} API permissions.")
    return service_dto


async def create_api_permission(data: CreateApiPermission, logger: logging.Logger):
    async with ConnectionManager() as session:
        try:
            new_api_permission = dto_to_api_permission_entity(data, logger)  # Convert DTO to entity
            session.add(new_api_permission)
            await session.commit()
            logger.info(f"API permission created: {new_api_permission}")

            # Fetch the newly created API permission
            return entity_to_api_permission_dto(new_api_permission, logger)

        except SQLAlchemyError as e:
            logger.error(f"Failed to create API permission: {e}")
            await session.rollback()
            raise

async def check_api_permission_name_exists(name: str, logger: logging.Logger) -> bool:
    async with ConnectionManager() as session:
        try:
            # Query the ApiPermissionEntity to check for existing permission name
            result = await session.execute(
                select(ApiPermissionEntity).filter_by(name=name)
            )
            # Check if any permission with the given name exists
            return result.scalars().first() is not None
        except SQLAlchemyError as e:
            logger.error(f"Database error while checking API permission name: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred.")


def dto_to_api_permission_entity(dto: CreateApiPermission, logger: logging.Logger) -> ApiPermissionEntity:
    logger.debug(f"Converting DTO to entity: {dto}")
    entity = ApiPermissionEntity(
        name=dto.name,
        method=dto.method,
        api_url=dto.api_url,
        description=dto.description,
        status=dto.status
    )
    logger.info(f"Converted DTO to entity: {entity}")
    return entity


def entity_to_api_permission_dto(entity: ApiPermissionEntity, logger: logging.Logger) -> ApiPermissionDTO:
    logger.debug(f"Converting entity to DTO: {entity}")

    dto = ApiPermissionDTO(
        id=entity.id,
        name=entity.name,
        method=entity.method,
        api_url=entity.api_url,
        description=entity.description,
        status=entity.status
    )

    logger.info(f"Converted entity to DTO: {dto}")
    return dto


async def check_update_api_permission_name_exists(name: str, exclude_id: int, logger: logging.Logger) -> bool:
    async with ConnectionManager() as session:
        try:
            existing_permission = await session.execute(
                select(ApiPermissionEntity).filter(ApiPermissionEntity.name == name, ApiPermissionEntity.id != exclude_id)
            )
            return existing_permission.scalars().first() is not None
        except SQLAlchemyError as e:
            logger.error(f"Database error while checking API permission name: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred.")

async def update_api_permission(api_permission_id: int, data: CreateApiPermission, logger: logging.Logger):
    async with ConnectionManager() as session:
        try:
            # Fetch the existing API permission
            existing_permission = await fetch_api_permission_with_relationships(api_permission_id, session, logger)
            if not existing_permission:
                logger.error(f"API permission with ID {api_permission_id} not found.")
                # raise HTTPException(status_code=404, detail="API permission not found")
                return None

            # Update the existing permission with new data
            existing_permission.name = data.name
            existing_permission.method = data.method
            existing_permission.api_url = data.api_url
            existing_permission.description = data.description
            existing_permission.status = data.status

            session.add(existing_permission)
            await session.commit()
            logger.info(f"API permission updated: {existing_permission}")
            return entity_to_api_permission_dto(existing_permission, logger)  # Return the updated entity or convert to DTO if needed

        except SQLAlchemyError as e:
            logger.error(f"Failed to update API permission: {e}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
        except Exception as e:
            logger.error(f"An unexpected error occurred while updating: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")


async def fetch_api_permission_with_relationships(api_permission_id: int, session, logger) -> ApiPermissionEntity:
    logger.info(f"Fetching API permission with ID: {api_permission_id}")

    try:
        # Fetch the API permission by ID with eager loading of related entities
        result = await session.execute(
            select(ApiPermissionEntity)
            .options(
                selectinload(ApiPermissionEntity.services)  # Eager load the services relationship
            )
            .filter(ApiPermissionEntity.id == api_permission_id)
        )

        api_permission = result.scalars().first()

        if api_permission:
            logger.info(f"Successfully retrieved API permission: {api_permission}")
        else:
            logger.warning(f"API permission with ID {api_permission_id} not found.")

        return api_permission

    except Exception as e:
        logger.error(f"Error occurred while fetching API permission with ID {api_permission_id}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching the API permission.")


async def get_all_api_permissions(logger: logging.Logger):
    async with ConnectionManager() as session:
        try:
            # Fetch all API permissions from the database with eager loading
            result = await session.execute(
                select(ApiPermissionEntity)
                .options(
                    selectinload(ApiPermissionEntity.services)  # Eager load related services
                )
            )
            api_permissions = result.scalars().all()  # Fetch all results

            if not api_permissions:
                logger.warning("No API permissions found.")
                return []  # Return an empty list if no API permissions are found

            logger.info(f"Retrieved {len(api_permissions)} API permissions.")
            return [entity_to_api_permission_dto(api_permission, logger) for api_permission in api_permissions]

        except SQLAlchemyError as e:
            logger.error(f"Database error occurred while fetching API permissions: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching API permissions: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")


async def get_api_permission_by_id(api_permission_id: int, logger: logging.Logger):
    async with ConnectionManager() as session:
        try:
            # Fetch the API permission by ID
            api_permission = await fetch_api_permission_with_relationships(api_permission_id, session, logger)
            if not api_permission:
                logger.error(f"API permission with ID {api_permission_id} not found.")
                # raise HTTPException(status_code=404, detail="API permission not found")
                return None
            logger.info(f"Retrieved API permission: {api_permission}")
            return entity_to_api_permission_dto(api_permission, logger)  # Return the entity or convert to DTO if needed

        except SQLAlchemyError as e:
            logger.error(f"Database error occurred while fetching API permission: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching API permission: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")

async def delete_api_permission(api_permission_id: int, logger: logging.Logger):
    async with ConnectionManager() as session:
        try:
            # Fetch the API permission by ID to ensure it exists
            api_permission = await fetch_api_permission_with_relationships(api_permission_id, session, logger)
            if not api_permission:
                logger.error(f"API permission with ID {api_permission_id} not found for deletion.")
                # raise HTTPException(status_code=404, detail="API permission not found.")
                return None

            # Proceed to delete the API permission
            await session.delete(api_permission)
            await session.commit()  # Commit the transaction

            logger.info(f"Successfully deleted API permission with ID {api_permission_id}.")

        except asyncpg.PostgresError as pg_exc:
            logger.error(f"Database error occurred while deleting API permission: {pg_exc}")
            raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
        except Exception as e:
            logger.error(f"An unexpected error occurred while deleting API permission: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")



async def check_service_exists(service_id: int, logger: logging.Logger):
    async with ConnectionManager() as session:
        result = await session.execute(select(ServiceEntity).filter_by(id=service_id))
        return result.scalars().first() is not None

async def check_permissions_exist(api_permission_ids: List[int], logger: logging.Logger):
    async with ConnectionManager() as session:
        result = await session.execute(select(ApiPermissionEntity).filter(ApiPermissionEntity.id.in_(api_permission_ids)))
        return len(result.scalars().all()) == len(api_permission_ids)


async def create_api_permissions_mapping(service_id: int, api_permission_ids: List[int], logger: logging.Logger):
    async with ConnectionManager() as session:
        # Fetch existing mappings to check for duplicates
        existing_mappings = await session.execute(
            select(ServiceApiPermissionsMapping).where(
                ServiceApiPermissionsMapping.service_id == service_id,
                ServiceApiPermissionsMapping.api_permission_id.in_(api_permission_ids)
            )
        )
        existing_mappings_ids = {mapping.api_permission_id for mapping in existing_mappings.scalars()}

        # Create mappings for the API permission IDs that do not already exist
        new_mappings = [
            ServiceApiPermissionsMapping(service_id=service_id, api_permission_id=api_permission_id)
            for api_permission_id in api_permission_ids
            if api_permission_id not in existing_mappings_ids
        ]

        # Add new mappings to the session
        for mapping in new_mappings:
            session.add(mapping)

        await session.commit()

        logger.info(f"API permissions mapped to service {service_id}: {api_permission_ids}")

        # Fetch the updated service from the database
        updated_service = await fetch_service_with_relationships(service_id, session, logger)

        # Convert the updated service entity to DTO
        service_dto = entity_to_service_dto(updated_service, logger)

        # Construct and return the ResponseBO
        return ResponseBO(
            code=201,  # HTTP status code for Created
            status="CREATED",
            data=service_dto,
            message="API permission mapping created successfully."
        )



async def get_api_permissions_by_service_id(service_id: int, logger: logging.Logger) -> Union[
    None, ResponseBO, List[ApiPermissionDTO]]:
    async with ConnectionManager() as session:
        try:
            # Fetch the service entity with related API permissions
            service = await fetch_service_with_relationships(service_id, session, logger)

            if not service:
                logger.error(f"Service with ID {service_id} not found.")
                # raise HTTPException(status_code=404, detail="Service not found")
                return None

            # Convert the API permissions to DTOs
            # api_permission_dtos = [
            #     entity_to_api_permission_dto(permission, logger) for permission in service.api_permissions
            # ]
            #
            # if not api_permission_dtos:
            #     logger.warning(f"No API permissions found for service ID {service_id}.")
            #     raise HTTPException(status_code=404, detail="No API permissions found for the service")
            api_permission_dtos = [
                entity_to_api_permission_dto(permission, logger) for permission in service.api_permissions
            ]

            if not api_permission_dtos:
                logger.warning(f"No API permissions found for service ID {service_id}.")
                return ResponseBO(
                    code=404,
                    status="NOT FOUND",
                    embedded=None,
                    message="No API permissions found for the service"
                )
            logger.info(f"Successfully retrieved {len(api_permission_dtos)} API permissions for service ID {service_id}")
            return ResponseBO(
                code=200,
                status="OK",
                embedded=api_permission_dtos,  # Use the embedded field to return the list of DTOs
                message=f"{len(api_permission_dtos)} API permissions retrieved successfully."
            )
            # return api_permission_dtos

        except SQLAlchemyError as e:
            logger.error(f"Database error occurred: {e}")
            raise HTTPException(status_code=500, detail="Database error. Please try again later.")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")





#Page Permissions

async def check_update_page_permission_name_exists(name: str, exclude_id: int, logger: logging.Logger) -> bool:
    async with ConnectionManager() as session:
        try:
            existing_permission = await session.execute(
                select(PagePermissionEntity).filter(PagePermissionEntity.name == name, PagePermissionEntity.id != exclude_id)
            )
            return existing_permission.scalars().first() is not None
        except SQLAlchemyError as e:
            logger.error(f"Database error while checking page permission name: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred.")


async def fetch_page_permission_with_relationships(page_permission_id: int, session, logger) -> PagePermissionEntity:
    logger.info(f"Fetching page permission with ID: {page_permission_id}")
    try:
        result = await session.execute(
            select(PagePermissionEntity)
            .options(
                selectinload(PagePermissionEntity.services),  # Eager load the services relationship
            )
            .filter(PagePermissionEntity.id == page_permission_id)
        )

        page_permission = result.scalars().first()

        if page_permission:
            logger.info(f"Successfully retrieved page permission: {page_permission}")
        else:
            logger.warning(f"Page Permission with ID {page_permission_id} not found.")

        return page_permission

    except Exception as e:
        logger.error(f"Error occurred while fetching page permission with ID {page_permission_id}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching the page permission.")

async def create_page_permission(data: PagePermissionDTO, logger: logging.Logger) -> PagePermissionDTO:
    async with ConnectionManager() as session:
        try:
            new_permission = dto_to_page_permission_entity(data)  # Convert DTO to entity
            session.add(new_permission)
            await session.commit()
            logger.info("Page permission created successfully.")
            return entity_to_page_permission_dto(new_permission)  # Convert entity back to DTO for the response
        except SQLAlchemyError as e:
            logger.error(f"Database error occurred while creating page permission: {e}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Failed to create page permission.")


async def update_page_permission(page_permission_id: int, data: PagePermissionCreateDTO,
                                 logger: logging.Logger):
    async with ConnectionManager() as session:
        try:
            permission = await session.get(PagePermissionEntity, page_permission_id)
            if not permission:
                logger.error(f"Page Permission with ID {page_permission_id} not found.")
                # raise HTTPException(status_code=404, detail=f"Page Permission with ID {page_permission_id} not found.")
                return None

            # Update entity fields using the DTO
            for key, value in data.dict().items():
                setattr(permission, key, value)

            await session.commit()
            logger.info(f"Page permission with ID {page_permission_id} updated successfully.")
            return entity_to_page_permission_dto(permission)  # Convert entity back to DTO for the response
        except SQLAlchemyError as e:
            logger.error(f"Database error occurred while updating page permission: {e}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Failed to update page permission.")


async def delete_page_permission(permission_id: int, logger: logging.Logger) -> Optional[ResponseBO]:
    async with ConnectionManager() as session:
        try:
            # Fetch the page permission by ID to ensure it exists
            page_permission = await fetch_page_permission_with_relationships(permission_id, session, logger)
            if not page_permission:
                logger.error(f"Page Permission with ID {permission_id} not found for deletion.")
                return ResponseBO(
                    code=404,  # HTTP status code for Not Found
                    status="NOT FOUND",
                    data=None,
                    message=f"Page Permission with ID {permission_id} not found."
                )

            # Proceed to delete the page permission
            await session.delete(page_permission)
            await session.commit()  # Commit the transaction
            logger.info(f"Successfully deleted page permission with ID {permission_id}.")

            # Return a response indicating successful deletion
            return ResponseBO(
                code=200,  # HTTP status code for OK
                status="DELETED",
                data=None,
                message=f"Page permission with ID {permission_id} deleted successfully."
            )

        except SQLAlchemyError as e:
            logger.error(f"Database error occurred while deleting page permission: {e}")
            await session.rollback()  # Rollback in case of error
            raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
        except Exception as e:
            logger.error(f"An unexpected error occurred while deleting page permission: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")


# Fetch a PagePermissionEntity by ID
async def get_page_permission_by_id(page_permission_id: int, logger: logging.Logger):
    async with ConnectionManager() as session:
        try:
            # Fetch the page permission by ID with relationships
            page_permission = await fetch_page_permission_with_relationships(page_permission_id, session, logger)
            if not page_permission:
                logger.error(f"Page Permission with ID {page_permission_id} not found.")
                # raise HTTPException(status_code=404, detail="Page Permission not found")
                return None
            logger.info(f"Retrieved Page Permission: {page_permission}")
            return entity_to_page_permission_dto(page_permission)  # Convert to DTO if needed

        except SQLAlchemyError as e:
            logger.error(f"Database error occurred while fetching page permission: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching page permission: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")


# Fetch all PagePermissionEntity records
async def get_all_page_permissions(logger: logging.Logger):
    async with ConnectionManager() as session:
        try:
            result = await session.execute(
                select(PagePermissionEntity)
                .options(
                    selectinload(PagePermissionEntity.services),  # Eager load related services
                )
            )
            page_permissions = result.scalars().all()

            if not page_permissions:
                logger.warning("No page permissions found.")
                return []  # Return empty list if none are found

            logger.info(f"Retrieved {len(page_permissions)} page permissions.")
            return [entity_to_page_permission_dto(page_permission) for page_permission in page_permissions]

        except SQLAlchemyError as e:
            logger.error(f"Database error occurred while fetching page permissions: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching page permissions: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")


async def check_page_permissions_exist(page_permission_ids: List[int], logger: logging.Logger):
    async with ConnectionManager() as session:
        # Use .in_() to check if page permissions exist
        result = await session.execute(
            select(PagePermissionEntity).filter(PagePermissionEntity.id.in_(page_permission_ids))
        )
        permissions = result.scalars().all()

        # Log the number of found permissions
        logger.info(f"Found {len(permissions)} page permissions for the given IDs.")

        # Return true if all permissions were found
        return len(permissions) == len(page_permission_ids)


async def create_page_permissions_mapping(service_id: int, page_permission_ids: List[int], logger: logging.Logger):
    async with ConnectionManager() as session:
        # Fetch existing mappings to avoid duplicates
        existing_mappings = await session.execute(
            select(ServiceApiPagePermissionsMapping).where(
                ServiceApiPagePermissionsMapping.service_id == service_id,
                ServiceApiPagePermissionsMapping.page_permission_id.in_(page_permission_ids)
            )
        )
        existing_mappings_ids = {mapping.page_permission_id for mapping in existing_mappings.scalars()}

        # Create new mappings for page permissions that are not already mapped
        new_mappings = [
            ServiceApiPagePermissionsMapping(service_id=service_id, page_permission_id=page_permission_id)
            for page_permission_id in page_permission_ids
            if page_permission_id not in existing_mappings_ids
        ]

        # Add new mappings to the session
        for mapping in new_mappings:
            session.add(mapping)

        await session.commit()

        logger.info(f"Page permissions mapped to service {service_id}: {page_permission_ids}")

        # Fetch the updated service from the database
        updated_service = await fetch_service_with_relationships(service_id, session, logger)

        # Convert the updated service entity to DTO
        service_dto = entity_to_service_dto(updated_service, logger)

        # Return the response
        return ResponseBO(
            code=201,  # HTTP status code for Created
            status="CREATED",
            data=service_dto,
            message="Page permission mapping created successfully."
        )

async def fetch_service_page_permission_with_relationships(service_id: int, session, logger) -> ServiceEntity:
    logger.info(f"Fetching service with ID: {service_id}")

    try:
        result = await session.execute(
            select(ServiceEntity)
            .options(selectinload(ServiceEntity.page_permissions))  # Eager load the page permissions
            .filter(ServiceEntity.id == service_id)
        )
        service = result.scalars().first()

        if service:
            logger.info(f"Successfully retrieved service: {service}")
        else:
            logger.warning(f"Service with ID {service_id} not found.")

        return service

    except Exception as e:
        logger.error(f"Error occurred while fetching service with ID {service_id}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching the service.")


def entity_to_page_permission_dto(entity: PagePermissionEntity) -> PagePermissionDTO:
    return PagePermissionDTO(
        id=entity.id,
        name=entity.name,
        description=entity.description,
        status=entity.status,
        page_url=entity.page_url
    )


def dto_to_page_permission_entity(dto: PagePermissionDTO) -> PagePermissionEntity:
    return PagePermissionEntity(
        name=dto.name,
        description=dto.description,
        status=dto.status,
        page_url=dto.page_url
    )
