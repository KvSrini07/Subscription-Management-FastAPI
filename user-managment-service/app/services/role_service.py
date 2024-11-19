# app/services/role_service.py

import logging
from fastapi import HTTPException
from sqlalchemy.orm import selectinload

from app.configuration.db import ConnectionManager
from app.models.models import RoleEntity, UserEntity
from app.models.pydantic_models import CreateRole, RoleDTO
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

class RoleService:

    @staticmethod
    async def check_role_exists(role_name: str, logger: logging.Logger):
        async with ConnectionManager() as session:
            try:
                # Query to check if a role with the same name exists
                existing_role = await session.execute(
                    select(RoleEntity).where(RoleEntity.role == role_name)
                )
                role = existing_role.scalar()

                if role:  # If a role is found, return conflict
                    logger.warning(f"Role with name '{role_name}' already exists.")
                    return True  # Conflict found

                return False  # No conflict, role does not exist

            except SQLAlchemyError as e:
                logger.error(f"Error while checking role existence: {e}")
                raise HTTPException(status_code=500, detail="An error occurred while checking role existence.")

    @staticmethod
    async def role_exists(session: AsyncSession, role: str, current_role_id: int) -> bool:
        """Check if the role exists in the database other than the given role ID."""
        stmt = select(RoleEntity).where(RoleEntity.role == role).where(RoleEntity.id != current_role_id)
        result = await session.execute(stmt)
        return result.scalars().first() is not None

    @staticmethod
    async def fetch_role_by_id(role_id: int, session, logger: logging.Logger) -> RoleEntity:
        """Fetch a role by its ID."""
        try:
            logger.info(f"Fetching role with ID: {role_id}")
            role = await session.get(RoleEntity, role_id)

            if role:
                logger.info(f"Role found: {role_id}")
            else:
                logger.warning(f"Role with ID {role_id} not found.")

            return role
        except SQLAlchemyError as e:
            logger.error(f"Error fetching role with ID {role_id}: {e}")
            raise Exception(f"Error fetching role with ID {role_id}: {e}")

    @staticmethod
    async def fetch_user_by_id(user_id: int, session, logger: logging.Logger) -> UserEntity:
        """Fetch a user by its ID."""
        try:
            logger.info(f"Fetching user with ID: {user_id}")
            result = await session.execute(
                select(UserEntity)
                .options(
                    selectinload(UserEntity.role)
                )
                .filter(UserEntity.id == user_id)
            )

            user = result.scalars().first()

            if user:
                logger.info(f"User found: {user_id}")
            else:
                logger.warning(f"User with ID {user_id} not found.")

            return user
        except SQLAlchemyError as e:
            logger.error(f"Error fetching user with ID {user_id}: {e}")
            raise Exception(f"Error fetching user with ID {user_id}: {e}")

    @staticmethod
    async def check_role_assigned_to_users(role_id: int, logger: logging.Logger):
        async with ConnectionManager() as session:
            try:
                # Query to check if any users are associated with the role_id
                users_with_role = await session.execute(
                    select(UserEntity).where(UserEntity.role_id == role_id)
                )
                users = users_with_role.scalars().all()

                if users:  # If users are found, return conflict
                    logger.warning(f"Role with ID {role_id} is assigned to {len(users)} users.")
                    return True  # Conflict found

                return False  # No conflict

            except SQLAlchemyError as e:
                logger.error(f"Error while checking role assignment: {e}")
                raise HTTPException(status_code=500, detail="An error occurred while checking role assignment.")

    async def create_role(self, data: CreateRole, logger: logging.Logger):
        async with ConnectionManager() as session:
            try:
                new_role = self.dto_to_entity(data, logger)
                session.add(new_role)
                await session.commit()
                await session.refresh(new_role)
                logger.info(f"Role created: {new_role}")
                return self.entity_to_dto(new_role, logger)
            except SQLAlchemyError as e:
                logger.error(f"Failed to create role: {e}")
                await session.rollback()
                raise

    async def update_role(self, role_id: int, data: CreateRole, logger: logging.Logger):
        async with ConnectionManager() as session:
            try:
                # Fetch the existing role
                existing_role = await self.fetch_role_by_id(role_id, session, logger)
                if not existing_role:
                    logger.error(f"Role with ID {role_id} not found.")
                    raise ValueError(f"Role with ID {role_id} not found.")

                # Update the role's fields with the new data
                for key, value in data.dict(exclude_unset=True).items():
                    setattr(existing_role, key, value)

                await session.commit()
                await session.refresh(existing_role)
                logger.info(f"Role updated: {existing_role}")
                return self.entity_to_dto(existing_role, logger)

            except SQLAlchemyError as e:
                logger.error(f"Failed to update role: {e}")
                await session.rollback()
                raise

    async def get_role_by_id(self, role_id: int, logger: logging.Logger):
        async with ConnectionManager() as session:
            try:
                role = await self.fetch_role_by_id(role_id, session, logger)
                if not role:
                    logger.error(f"Role with ID {role_id} not found.")
                    return None

                logger.info(f"Role found: {role}")
                return self.entity_to_dto(role, logger)  # Convert the entity to DTO before returning

            except SQLAlchemyError as e:
                logger.error(f"Database error occurred while retrieving role: {e}")
                raise

    async def get_role_by_user_id(self, user_id: int, logger: logging.Logger):
        async with ConnectionManager() as session:
            try:
                user = await self.fetch_user_by_id(user_id, session, logger)
                if not user:
                    logger.error(f"User with ID {user_id} not found.")
                    return None

                logger.info(f"Role found for user ID {user_id}: {user.role.role}")
                return self.entity_to_dto(user.role, logger)  # Convert the entity to DTO before returning

            except SQLAlchemyError as e:
                logger.error(f"Database error occurred while retrieving role for user ID {user_id}: {e}")
                raise

    async def get_all_roles(self, logger: logging.Logger):
        async with ConnectionManager() as session:
            try:
                roles = await session.execute(select(RoleEntity))  # Assuming you are using SQLAlchemy
                roles_list = roles.scalars().all()  # Get all roles

                logger.info(f"Total roles found: {len(roles_list)}")
                return [self.entity_to_dto(role, logger) for role in roles_list]  # Convert each entity to DTO

            except SQLAlchemyError as e:
                logger.error(f"Database error occurred while retrieving roles: {e}")
                raise

    async def delete_role(self, role_id: int, logger: logging.Logger):
        """Delete a role by its ID."""
        async with ConnectionManager() as session:
            try:
                # Fetch the role using the separate function
                role = await self.fetch_role_by_id(role_id, session, logger)

                if not role:
                    logger.error(f"Role with ID {role_id} not found.")
                    return None

                # Proceed with deletion
                await session.delete(role)  # Delete the role
                await session.commit()  # Commit the changes
                logger.info(f"Role deleted: {role_id}")
                return True  # Indicate success

            except SQLAlchemyError as e:
                logger.error(f"Failed to delete role: {e}")
                await session.rollback()  # Rollback in case of an error
                raise

    @staticmethod
    def entity_to_dto(role_entity: RoleEntity, logger) -> RoleDTO:
        logger.debug(f"Converting RoleEntity to RoleDTO: {role_entity}")
        dto = RoleDTO(
            id=role_entity.id,
            role=role_entity.role,
            description=role_entity.description
        )
        logger.info(f"Converted RoleEntity to RoleDTO: {dto}")
        return dto

    @staticmethod
    def dto_to_entity(role_dto: CreateRole, logger) -> RoleEntity:
        logger.debug(f"Converting CreateRole DTO to RoleEntity: {role_dto}")
        entity = RoleEntity(
            role=role_dto.role,
            description=role_dto.description
        )
        logger.info(f"Converted CreateRole DTO to RoleEntity: {entity}")
        return entity