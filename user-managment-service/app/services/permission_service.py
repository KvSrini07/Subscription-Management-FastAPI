# app/services/permission_service.py
import json
import logging
from typing import Optional, Type
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from app.configuration.db import ConnectionManager
from app.models.models import PermissionEntity, UserEntity, OrganizationEntity, OrganizationSubscriptionEntity, \
    SubscriptionEntity, ServiceEntity
from app.models.pydantic_models import UpdatePermission, PermissionDTO, AddressDTO, SubscriptionDTO, ServiceDTO, \
    ApiPermissionDTO, OrganizationSubscriptionDTO, OrganizationDTO, LoginDTO, RoleDTO, PermissionUser
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

class PermissionService:

    # @staticmethod
    # async def permission_exists(session: AsyncSession, permission_name: str, current_permission_id: int) -> bool:
    #     """Check if the permission exists in the database other than the given permission ID."""
    #     stmt = select(PermissionEntity).where(PermissionEntity.name == permission_name).where(
    #         PermissionEntity.id != current_permission_id)
    #     result = await session.execute(stmt)
    #     return result.scalars().first() is not None

    @staticmethod
    async def fetch_permission_entity_by_id(permission_id: int, session, logger: logging.Logger) -> PermissionEntity:
        """Fetch the permission entity from the database by its ID."""
        try:
            # Fetch the permission entity by ID, eager loading all necessary relationships
            result = await session.execute(
                select(PermissionEntity)
                .options(
                    selectinload(PermissionEntity.user)
                    .selectinload(UserEntity.address),
                    selectinload(PermissionEntity.user)
                    .selectinload(UserEntity.organization)
                    .selectinload(OrganizationEntity.organization_subscription)
                    .selectinload(OrganizationSubscriptionEntity.subscription)
                    .selectinload(SubscriptionEntity.services)
                    .selectinload(ServiceEntity.api_permissions),
                    selectinload(PermissionEntity.user)
                    .selectinload(UserEntity.role),
                    selectinload(PermissionEntity.user)
                    .selectinload(UserEntity.login)
                )
                .filter(PermissionEntity.id == permission_id)
            )

            # Extract the permission entity from the result
            permission_entity = result.scalar_one_or_none()

            # If the permission entity is not found, raise a 404 error
            if not permission_entity:
                logger.error(f"Permission with ID {permission_id} not found.")
                raise HTTPException(status_code=404, detail=f"Permission with ID {permission_id} not found.")

            logger.info(f"Permission with ID {permission_id} successfully fetched.")
            return permission_entity

        except Exception as e:
            logger.error(f"Error fetching permission entity with ID {permission_id}: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching the permission.")

    @staticmethod
    async def check_permission_assigned_to_users(permission_id: int, logger: logging.Logger):
        async with ConnectionManager() as session:
            try:
                # Query to check if any users are associated with the permission_id
                users_with_permission = await session.execute(
                    select(UserEntity).where(UserEntity.permission_id == permission_id)
                )
                users = users_with_permission.scalars().all()

                if users:  # If users are found, return conflict
                    logger.warning(f"Permission with ID {permission_id} is assigned to {len(users)} users.")
                    return True  # Conflict found

                return False  # No conflict

            except SQLAlchemyError as e:
                logger.error(f"Error while checking permission assignment: {e}")
                raise HTTPException(status_code=500, detail="An error occurred while checking permission assignment.")

    async def update_permission(self, permission_id: int, data: UpdatePermission, logger: logging.Logger):
        async with ConnectionManager() as session:
            try:
                # Fetch the existing permission
                existing_permission = await self.fetch_permission_entity_by_id(permission_id, session, logger)
                if not existing_permission:
                    logger.error(f"Permission with ID {permission_id} not found.")
                    return None

                # Update the permission's fields with the new data
                for key, value in data.dict(exclude_unset=True).items():
                    setattr(existing_permission, key, value)

                await session.commit()
                await session.refresh(existing_permission)
                logger.info(f"Permission updated: {existing_permission}")
                return self.entity_to_dto(existing_permission, logger)

            except SQLAlchemyError as e:
                logger.error(f"Failed to update permission: {e}")
                await session.rollback()
                raise

    async def get_permission_by_id(self, permission_id: int, session: AsyncSession, logger: logging.Logger) -> PermissionDTO:
        """Retrieve a permission by its ID and return it as a DTO."""
        try:
            # Use the separate function to fetch the entity
            permission_entity = await self.fetch_permission_entity_by_id(permission_id, session, logger)

            # Convert the entity to a DTO
            permission_dto = self.entity_to_dto(permission_entity, logger)
            logger.info(f"Successfully converted permission entity with ID {permission_id} to DTO.")
            return permission_dto

        except HTTPException as http_exc:
            logger.error(f"HTTPException occurred: {http_exc.detail}")
            raise http_exc
        except Exception as e:
            logger.error(f"Error processing permission with ID {permission_id}: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred while processing the permission.")

    async def get_all(self, logger: logging.Logger, page: int, size: int, search_key: Optional[str] = None):
        async with ConnectionManager() as session:
            try:
                logger.info(
                    f"Fetching permissions with pagination - page: {page}, size: {size}, searchKey: {search_key}")

                # Define the query with the updated relationships and entities
                query = select(PermissionEntity).options(
                    selectinload(PermissionEntity.user)
                    .selectinload(UserEntity.address),  # Loading UserEntity's Address
                    selectinload(PermissionEntity.user)
                    .selectinload(UserEntity.organization)
                    .selectinload(OrganizationEntity.organization_subscription)
                    .selectinload(OrganizationSubscriptionEntity.subscription)
                    .selectinload(SubscriptionEntity.services)
                    .selectinload(ServiceEntity.api_permissions),  # Loading ServiceEntity's ApiPermissions
                    selectinload(PermissionEntity.user)
                    .selectinload(UserEntity.role),  # Loading UserEntity's Role
                    selectinload(PermissionEntity.user)
                    .selectinload(UserEntity.login)  # Loading UserEntity's Login
                )

                # Apply search_key if provided to filter permissions by name
                if search_key:
                    query = query.where(
                        PermissionEntity.name.ilike(f"%{search_key}%")
                    )

                # Fetch total count of filtered permissions
                total_elements_query = select(func.count()).select_from(query.subquery())
                total_elements = await session.execute(total_elements_query)
                total_elements = total_elements.scalar()

                # Apply pagination to the query
                paginated_query = query.offset((page - 1) * size).limit(size)
                result = await session.execute(paginated_query)
                permissions = result.scalars().all()

                if permissions:
                    logger.info(f"{len(permissions)} permissions found on page {page}")
                    permissions_dto = [self.entity_to_dto(permission, logger) for permission in permissions]

                    # Returning paginated data
                    return {
                        "data": permissions_dto,
                        "total_pages": (total_elements // size) + (1 if total_elements % size > 0 else 0),
                        "total_elements": total_elements
                    }
                else:
                    logger.warning("No permissions found")
                    return {
                        "data": [],
                        "total_pages": 0,
                        "total_elements": 0
                    }

            except SQLAlchemyError as e:
                logger.error(f"Failed to fetch permissions, error: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error during get_all_permissions: {e}")
                raise

    async def delete_permission(self, permission_id: int, logger: logging.Logger):
        async with ConnectionManager() as session:
            try:
                permission = await self.fetch_permission_entity_by_id(permission_id, session, logger)
                if not permission:
                    logger.error(f"Permission with ID {permission_id} not found.")
                    return None

                await session.delete(permission)  # Delete the permission
                await session.commit()  # Commit the changes
                logger.info(f"Permission deleted: {permission_id}")
                return True  # Indicate success

            except SQLAlchemyError as e:
                logger.error(f"Failed to delete permission: {e}")
                await session.rollback()  # Rollback in case of an error
                raise

    @staticmethod
    def entity_to_dto(permission_entity: PermissionEntity, logger: logging.Logger) -> PermissionDTO:
        """Convert a PermissionEntity to PermissionDTO."""
        try:
            logger.debug("Starting conversion of PermissionEntity to PermissionDTO for permission id: %s",
                         permission_entity.id)

            # Mapping AddressEntity to AddressDTO if the permission's user has an address
            address_dto = AddressDTO(
                id=permission_entity.user.address.id if permission_entity.user and permission_entity.user.address else None,
                address_line_1=permission_entity.user.address.address_line_1 if permission_entity.user and permission_entity.user.address else None,
                address_line_2=permission_entity.user.address.address_line_2 if permission_entity.user and permission_entity.user.address else None,
                city=permission_entity.user.address.city if permission_entity.user and permission_entity.user.address else None,
                state=permission_entity.user.address.state if permission_entity.user and permission_entity.user.address else None,
                country=permission_entity.user.address.country if permission_entity.user and permission_entity.user.address else None,
                pincode=permission_entity.user.address.pincode if permission_entity.user and permission_entity.user.address else None,
                reference_id=permission_entity.user.address.reference_id if permission_entity.user and permission_entity.user.address else None
            ) if permission_entity.user else None
            logger.debug("Mapped AddressEntity to AddressDTO: %s", address_dto)

            # Mapping OrganizationSubscriptionEntity to OrganizationSubscriptionDTO if the permission's user has an organization subscription
            organization_subscription_dto = None
            if permission_entity.user and permission_entity.user.organization and permission_entity.user.organization.organization_subscription:
                org_sub = permission_entity.user.organization.organization_subscription

                subscription_dto = SubscriptionDTO(
                    id=org_sub.subscription.id if org_sub.subscription else None,
                    name=org_sub.subscription.name if org_sub.subscription else None,
                    validity=org_sub.subscription.validity if org_sub.subscription else None,
                    cost=org_sub.subscription.cost if org_sub.subscription else None,
                    active_status=org_sub.subscription.active_status if org_sub.subscription else None,
                    subscription_type=org_sub.subscription.subscription_type.name if org_sub.subscription.subscription_type else None,
                    services=[ServiceDTO(
                        id=service.id,
                        name=service.name,
                        description=service.description,
                        active_status=service.active_status,
                        api_permissions=[
                            ApiPermissionDTO(
                                id=api_permission.id,
                                name=api_permission.name,
                                method=api_permission.method,
                                api_url=api_permission.api_url,
                                description=api_permission.description,
                                status=api_permission.status
                            )
                            for api_permission in service.api_permissions
                        ] if service.api_permissions else None
                    ) for service in
                        org_sub.subscription.services] if org_sub.subscription and org_sub.subscription.services else None,
                )

                organization_subscription_dto = OrganizationSubscriptionDTO(
                    id=org_sub.id,
                    subscription_date=org_sub.subscription_date,
                    subscription=subscription_dto
                )
                logger.debug("Mapped OrganizationSubscriptionEntity to OrganizationSubscriptionDTO: %s",
                             organization_subscription_dto)

            # Adding the organization_subscription_dto to the organization_dto
            organization_dto = OrganizationDTO(
                id=permission_entity.user.organization.id if permission_entity.user.organization else None,
                organization_name=permission_entity.user.organization.organization_name if permission_entity.user.organization else None,
                display_name=permission_entity.user.organization.display_name if permission_entity.user.organization else None,
                gstin=permission_entity.user.organization.gstin if permission_entity.user.organization else None,
                pan=permission_entity.user.organization.pan if permission_entity.user.organization else None,
                tan=permission_entity.user.organization.tan if permission_entity.user.organization else None,
                organization_type=permission_entity.user.organization.organization_type if permission_entity.user.organization else None,
                incorporation_date=permission_entity.user.organization.incorporation_date if permission_entity.user.organization else None,
                cin=permission_entity.user.organization.cin if permission_entity.user.organization else None,
                organization_subscription=organization_subscription_dto  # Add the subscription here
            )

            # Mapping LoginEntity to LoginDTO if the permission's user has a login
            login_dto = LoginDTO(
                id=permission_entity.user.login.id if permission_entity.user and permission_entity.user.login else None,
                username=permission_entity.user.login.username if permission_entity.user and permission_entity.user.login else None,
                password=None,  # Avoid exposing the password
                account_active=permission_entity.user.login.account_active if permission_entity.user and permission_entity.user.login else None,
                account_inactive_reason=permission_entity.user.login.account_inactive_reason if permission_entity.user and permission_entity.user.login else None,
                login_time=permission_entity.user.login.login_time if permission_entity.user and permission_entity.user.login else None,
                logout_time=permission_entity.user.login.logout_time if permission_entity.user and permission_entity.user.login else None
            ) if permission_entity.user else None
            logger.debug("Mapped LoginEntity to LoginDTO: %s", login_dto)

            # Mapping RoleEntity to RoleDTO if the permission's user has a role
            role_dto = RoleDTO(
                id=permission_entity.user.role.id if permission_entity.user and permission_entity.user.role else None,
                role=permission_entity.user.role.role if permission_entity.user and permission_entity.user.role else None,
                description=permission_entity.user.role.description if permission_entity.user and permission_entity.user.role else None
            ) if permission_entity.user else None
            logger.debug("Mapped RoleEntity to RoleDTO: %s", role_dto)

            # Creating PermissionUser DTO from the above mappings
            permission_user_dto = PermissionUser(
                id=permission_entity.user.id if permission_entity.user else None,
                customer_id=permission_entity.user.customer_id if permission_entity.user else None,
                first_name=permission_entity.user.first_name if permission_entity.user else None,
                last_name=permission_entity.user.last_name if permission_entity.user else None,
                email_id=permission_entity.user.email_id if permission_entity.user else None,
                mobile_no=permission_entity.user.mobile_no if permission_entity.user else None,
                address=address_dto,
                organization=organization_dto,
                login=login_dto,
                role=role_dto
            ) if permission_entity.user else None
            logger.debug("Mapped UserEntity to PermissionUser DTO: %s", permission_user_dto)

            # Creating PermissionDTO from the above mappings
            permission_dto = PermissionDTO(
                id=permission_entity.id,
                name=permission_entity.name,
                permission=json.loads(permission_entity.permission) if permission_entity.permission else {},
                user=permission_user_dto
            )
            logger.debug("Successfully created PermissionDTO: %s", permission_dto)

            return permission_dto

        except Exception as e:
            logger.error(f"Error converting PermissionEntity to PermissionDTO: {e}")
            raise ValueError("Failed to convert PermissionEntity to DTO")


