# import logging
# from datetime import date
# from typing import Union, Optional
#
# from fastapi import HTTPException
# from sqlalchemy import func, or_, String
# from sqlalchemy.exc import NoResultFound
# from sqlalchemy.orm import joinedload, selectinload
# from app.configuration.db import ConnectionManager
# from app.models.models import UserEntity, AddressEntity, OrganizationEntity, LoginEntity, RoleEntity, \
#     SubscriptionEntity, OrganizationSubscriptionEntity, PermissionEntity, ApiPermissionEntity, ServiceEntity
# from app.models.pydantic_models import Register, CreateUser, UpdateUser, AddressDTO, \
#     OrganizationDTO, UserDTO, LoginDTO, RoleDTO, PermissionDTO, OrganizationSubscriptionDTO, SubscriptionDTO, \
#     ServiceDTO, ApiPermissionDTO, UserPermission
# import random
# import string
# import os
# import json
# from sqlalchemy.future import select
# from sqlalchemy.exc import SQLAlchemyError
#
# class UserService:
#
#     @staticmethod
#     async def is_user_identifier_exists(session, logger, identifier: str, field: str) -> bool:
#         logger.info(f"Checking if {field} exists: {identifier}")
#         # Check existence in UserEntity
#         result = await session.execute(
#             select(UserEntity).filter(getattr(UserEntity, field) == identifier)  # Dynamic field access on UserEntity
#         )
#         exists = result.scalars().first() is not None
#         logger.info(f"{field.upper()} exists in UserEntity: {exists} for {field}: {identifier}")
#         return exists
#
#     @staticmethod
#     async def is_organization_identifier_exists(session, logger, identifier: str, field: str) -> bool:
#         logger.info(f"Checking if {field} exists: {identifier}")
#         # Check existence in OrganizationEntity
#         result = await session.execute(
#             select(UserEntity)
#             .join(UserEntity.organization)  # Join with OrganizationEntity
#             .filter(getattr(OrganizationEntity, field) == identifier)  # Dynamic field access
#             .options(joinedload(UserEntity.organization))  # Eager load the organization relationship
#         )
#         exists = result.scalars().first() is not None
#         logger.info(f"{field.upper()} exists in OrganizationEntity: {exists} for {field}: {identifier}")
#         return exists
#
#     @staticmethod
#     async def check_unique_value(session, model, field_name, value, exclude_id=None):
#         """
#         Check if a given value is unique in the specified model (table).
#         :param session: Database session
#         :param model: SQLAlchemy model class to check against
#         :param field_name: The field to check for uniqueness
#         :param value: The value to check
#         :param exclude_id: The id to exclude from the check (for updates)
#         :return: True if unique, False if exists
#         """
#         try:
#             query = select(model).filter(getattr(model, field_name) == value)
#             if exclude_id:
#                 query = query.filter(model.id != exclude_id)
#
#             result = await session.execute(query)
#             return result.scalars().first() is None  # Return True if no record found
#
#         except SQLAlchemyError as e:
#             raise Exception(f"Database error during uniqueness check: {e}")
#
#     @staticmethod
#     async def generate_customer_id(session) -> str:
#         try:
#             result = await session.execute(select(UserEntity.customer_id).order_by(UserEntity.id.desc()).limit(1))
#             last_customer_id = result.scalars().first()
#             new_customer_id = (int(last_customer_id) + 1) if last_customer_id else 1
#             formatted_customer_id = f"{new_customer_id:06d}"  # Format to 6 digits
#             logging.debug(f"Generated new customer ID: {formatted_customer_id}")
#             return formatted_customer_id
#         except Exception as e:
#             logging.error(f"Error generating customer ID: {e}")
#             raise
#
#     @staticmethod
#     async def find_by_role(session, role_name: str, logger: logging.Logger):
#         try:
#             role = await session.execute(
#                 select(RoleEntity).where(RoleEntity.role == role_name)
#             )
#             result = role.scalars().first()
#             if not result:
#                 logger.error(f"Role '{role_name}' not found.")
#                 raise ValueError(f"Role '{role_name}' does not exist.")
#             return result
#         except SQLAlchemyError as e:
#             logger.error(f"Database error while retrieving role: {e}")
#             raise
#
#     @staticmethod
#     async def find_subscription_by_id(session, subscription_id: int, logger: logging.Logger):
#         logger.info(f"Fetching subscription with ID: {subscription_id}")
#
#         try:
#             # Fetch the subscription by ID with eager loading of related entities
#             result = await session.execute(
#                 select(SubscriptionEntity)
#                 .options(
#                     selectinload(SubscriptionEntity.services)  # Eager load the services relationship
#                     .selectinload(ServiceEntity.api_permissions)  # Eager load related ApiPermissionEntity
#                 )
#                 .filter(SubscriptionEntity.id == subscription_id)
#             )
#
#             subscription = result.scalars().first()
#
#             if subscription:
#                 logger.info(f"Successfully retrieved subscription: {subscription}")
#             else:
#                 logger.warning(f"Subscription with ID {subscription_id} not found.")
#
#             return subscription
#
#         except Exception as e:
#             logger.error(f"Error occurred while fetching subscription with ID {subscription_id}: {e}")
#             raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching the subscription.")
#
#     @staticmethod
#     def generate_strong_password() -> str:
#
#         password_length = 8
#
#         # Define character sets
#         lowercase = string.ascii_lowercase
#         uppercase = string.ascii_uppercase
#         digits = string.digits
#         special_characters = string.punctuation
#
#         # Ensure the password contains at least one of each character type
#         password = [
#             random.choice(lowercase),
#             random.choice(uppercase),
#             random.choice(digits),
#             random.choice(special_characters)
#         ]
#
#         # Fill the rest of the password length with random choices from all character sets
#         all_characters = lowercase + uppercase + digits + special_characters
#         password += random.choices(all_characters, k=password_length - len(password))
#
#         # Shuffle the generated password to ensure randomness
#         random.shuffle(password)
#
#         return ''.join(password)
#
#     @staticmethod
#     async def is_organization_mapped_to_multiple_users(session, organization_id: int, logger) -> bool:
#         logger.info(f"Checking if organization ID {organization_id} is mapped to multiple users")
#
#         # Query to count the number of users associated with the given organization_id
#         result = await session.execute(
#             select(func.count(UserEntity.id))
#             .filter(UserEntity.organization_id == organization_id)  # Filter by organization_id
#         )
#
#         user_count = result.scalar()  # Get the count of users
#         has_multiple_users = user_count > 1  # Check if more than one user exists
#         logger.info(f"Organization ID {organization_id} has multiple users: {has_multiple_users} (Count: {user_count})")
#
#         return has_multiple_users
#
#     @staticmethod
#     async def fetch_existing_user(session, user_id, logger):
#         logger.info(f"Fetching user with ID: {user_id}")
#
#         try:
#             result = await session.execute(
#                 select(UserEntity)
#                 .options(
#                     selectinload(UserEntity.address),
#                     selectinload(UserEntity.organization)
#                     .selectinload(OrganizationEntity.organization_subscription)  # Eager load organization_subscription
#                     .selectinload(OrganizationSubscriptionEntity.subscription)
#                     .selectinload(SubscriptionEntity.services)
#                     .selectinload(ServiceEntity.api_permissions),
#                     selectinload(UserEntity.role),
#                     selectinload(UserEntity.login),
#                     selectinload(UserEntity.permission)  # Eager loading for permissions
#                 )
#                 .filter(UserEntity.id == user_id)
#             )
#
#             user = result.scalars().first()
#
#             if user:
#                 logger.info(f"User with ID {user_id} found: {user}")
#             else:
#                 logger.warning(f"User with ID {user_id} not found.")
#
#             return user
#
#         except Exception as e:
#             logger.error(f"Error fetching user with ID {user_id}: {e}")
#             raise
#
#     @staticmethod
#     async def fetch_existing_user_by_username(session, username: str, logger):
#         logger.info(f"Fetching user with username: {username}")
#
#         try:
#             result = await session.execute(
#                 select(UserEntity)
#                 .options(
#                     selectinload(UserEntity.address),
#                     selectinload(UserEntity.organization)
#                     .selectinload(OrganizationEntity.organization_subscription)  # Eager load organization_subscription
#                     .selectinload(OrganizationSubscriptionEntity.subscription)
#                     .selectinload(SubscriptionEntity.services)
#                     .selectinload(ServiceEntity.api_permissions),
#                     selectinload(UserEntity.role),
#                     selectinload(UserEntity.login),
#                     selectinload(UserEntity.permission)  # Eager loading for permissions
#                 )
#                 .filter(UserEntity.login.has(LoginEntity.username == username))  # Filtering by username
#             )
#
#             user = result.scalars().first()
#
#             if user:
#                 logger.info(f"User with username {username} found: {user}")
#             else:
#                 logger.warning(f"User with username {username} not found.")
#
#             return user
#
#         except Exception as e:
#             logger.error(f"Error fetching user with username {username}: {e}")
#             raise
#
#     @staticmethod
#     async def fetch_users_by_role_id(session, role_id: int, logger):
#         logger.info(f"Fetching users with role ID: {role_id}")
#
#         try:
#             result = await session.execute(
#                 select(UserEntity)
#                 .options(
#                     selectinload(UserEntity.address),
#                     selectinload(UserEntity.organization)
#                     .selectinload(OrganizationEntity.organization_subscription)  # Eager load organization_subscription
#                     .selectinload(OrganizationSubscriptionEntity.subscription)
#                     .selectinload(SubscriptionEntity.services)
#                     .selectinload(ServiceEntity.api_permissions),
#                     selectinload(UserEntity.role),
#                     selectinload(UserEntity.login),
#                     selectinload(UserEntity.permission)  # Eager loading for permissions
#                 )
#                 .filter(UserEntity.role_id == role_id)  # Filtering by role ID
#             )
#
#             users = result.scalars().all()
#
#             if users:
#                 logger.info(f"Users with role ID {role_id} found: {users}")
#             else:
#                 logger.warning(f"No users found with role ID {role_id}.")
#
#             return users
#
#         except Exception as e:
#             logger.error(f"Error fetching users with role ID {role_id}: {e}")
#             raise
#
#     @staticmethod
#     def api_permission_to_json(permission: ApiPermissionEntity):
#         return {
#             "name": permission.name,
#             "method": permission.method.value,  # If method is an Enum, use `.value`
#             "api_url": permission.api_url,
#             "description": permission.description,
#             "status": permission.status
#         }
#
#     async def register(self, data: Register, logger: logging.Logger):
#         async with ConnectionManager() as session:
#             try:
#                 logger.debug(f"Registering user with data: {data}")
#                 new_user = self.dto_to_entity(data, logger)
#
#                 # Generate customer ID
#                 customer_id = await self.generate_customer_id(session)
#                 new_user.customer_id = customer_id
#
#                 # Find the role entity based on the role provided in the data
#                 role_name = os.getenv('ROLE_ADMIN')
#                 new_user.role = await self.find_by_role(session, role_name, logger)
#
#                 # Find and set subscription
#                 subscription = await self.find_subscription_by_id(session, data.subscription_id, logger)
#
#                 # Convert organization DTO to entity
#                 organization = self.organization_dto_to_entity(data.organization, subscription)
#                 new_user.organization = organization
#
#                 # Create login entity and set it to new_user
#                 new_user.login = await self.create_login(new_user, logger)
#
#                 # Add new_user and related entities to the session
#                 session.add_all([new_user.address, new_user.organization.organization_subscription.subscription, new_user.organization, new_user.login, new_user])
#
#                 # Commit all changes
#                 await session.commit()
#
#                 # Now that the new_user has been committed, we can access its ID
#                 user_id = new_user.id
#
#                 # Set reference_id for the address
#                 new_user.address.reference_id = str(user_id)
#
#                 await session.commit()
#
#                 # Create PermissionEntity and set default values
#                 new_permission = PermissionEntity()
#                 new_permission.name = "API_USER"
#
#                 # Use the build_module_dict method to structure the permissions
#                 module_dict = self.build_module_dict(new_user)
#
#                 # Convert the dictionary to a JSON formatted string
#                 new_permission.permission = json.dumps(module_dict, indent=2)
#
#                 # Assign the permission to the user
#                 new_permission.user = new_user
#                 # new_user.permission = new_permission
#
#                 session.add(new_permission)
#
#                 # Now, commit again to save the reference ID
#                 await session.commit()
#
#                 logger.info(f"User registered successfully with ID: {user_id}")
#
#                 # Convert entity to DTO before returning
#                 return await self.entity_to_dto(new_user, logger)
#
#             except SQLAlchemyError as e:
#                 logger.error(f"Failed to register user: {e}")
#                 await session.rollback()
#                 raise
#             except Exception as e:
#                 logger.error(f"Unexpected error during registration: {e}")
#                 await session.rollback()
#                 raise
#
#     def build_module_dict(self, new_user: UserEntity):
#         # Initialize a dictionary to store modules and their actions
#         module_dict = {
#             "subscription_module": [],
#             "user_module": []
#         }
#
#         # Mapping keywords to module names and their constant IDs
#         keyword_to_info = {
#             "subscription": ("Subscription Module", "subscription_01"),
#             "service": ("Service Module", "service_01"),
#             "api_permission": ("API Permission Module", "api_permission_01"),
#             "user": ("User Module", "user_01"),
#             "role": ("Role Module", "role_01"),
#             "permission": ("Permission Module", "permission_01")
#         }
#
#         # Helper function to create or update a module entry
#         def add_module_entry(target_module_key, mod_id, mod_name, mod_parent_id, action):
#             module = next((m for m in module_dict[target_module_key] if m['id'] == mod_id), None)
#             if module:
#                 module["actions"].append(action)  # Add action to existing module
#             else:
#                 module_dict[target_module_key].append({
#                     "id": mod_id,
#                     "name": mod_name,
#                     "parentId": mod_parent_id,
#                     "actions": [action]
#                 })
#
#         # Iterate over the services and map permissions to modules
#         for service in new_user.organization.organization_subscription.subscription.services:
#             for permission in service.api_permissions:
#                 permission_name_lower = permission.name.lower()
#                 action_json = self.api_permission_to_json(permission)
#
#                 # Check and assign the correct module and IDs
#                 for keyword, (module_name, module_id) in keyword_to_info.items():
#                     if keyword in permission_name_lower:
#                         target_module = "subscription_module" if keyword in ["subscription", "service",
#                                                                              "api_permission"] else "user_module"
#
#                         # Set parentId based on the keyword logic
#                         parent_id = None
#                         if keyword == "subscription":
#                             parent_id = None  # No parent for subscription
#                         elif keyword == "service":
#                             parent_id = "subscription_01"  # Parent is subscription
#                         elif keyword == "api_permission":
#                             parent_id = "service_01"  # Parent is service
#                         elif keyword == "user":
#                             parent_id = None  # No parent for user
#                         elif keyword == "role":
#                             parent_id = "user_01"  # Parent is user
#                         elif keyword == "permission":
#                             parent_id = "role_01"  # Parent is role
#
#                         add_module_entry(target_module, module_id, module_name, parent_id, action_json)
#                         break  # Break after processing the first matching keyword
#
#         return module_dict
#
#     async def create_user(self, data: CreateUser, logger: logging.Logger):
#         async with ConnectionManager() as session:
#             try:
#                 # Convert DTO to Entity
#                 logger.debug(f"Registering user with data: {data}")
#                 new_user = self.dto_to_entity(data, logger)
#
#                 # Generate customer ID
#                 customer_id = await self.generate_customer_id(session)
#                 new_user.customer_id = customer_id
#
#                 # Find the role entity based on the role provided in the data
#                 role_name = os.getenv('ROLE_USER')  # Assuming `data` contains the role name
#                 new_user.role = await self.find_by_role(session, role_name, logger)  # Set the role for new_user
#
#                 # Find the existing user by ID to get their organization
#                 existing_user = await self.fetch_existing_user(session, data.admin_id, logger)
#                 if existing_user.organization:
#                     new_user.organization = existing_user.organization  # Set new_user's organization to existing_user's organization
#                 else:
#                     logger.error(f"User with ID {data.organization_id} not found.")
#                     raise ValueError(f"User with ID {data.organization_id} not found.")
#
#                 # Create login entity and add it to session
#                 new_user.login = await self.create_login(new_user, logger)
#
#                 # Add new_user and related entities to the session
#                 session.add_all([new_user.address, new_user.login, new_user])
#
#                 # Commit all changes
#                 await session.commit()
#
#                 # Now that the new_user has been committed, we can access its ID
#                 user_id = new_user.id
#
#                 # Set reference_id for the address
#                 new_user.address.reference_id = str(user_id)
#
#                 if existing_user.permission:
#                     new_permission = PermissionEntity(
#                         name=existing_user.permission.name,
#                         permission=existing_user.permission.permission
#                     )
#                     new_permission.user = new_user
#                 else:
#                     logger.error(f"User with ID {data.organization_id} not found.")
#                     raise ValueError(f"User with ID {data.organization_id} not found.")
#
#                 session.add_all([new_user.address, new_permission])
#
#                 # Now, commit again to save the reference ID
#                 await session.commit()
#
#                 logger.info(f"User registered successfully: {new_user}")
#
#                 return await self.entity_to_dto(new_user, logger)
#             except SQLAlchemyError as e:
#                 logger.error(f"Failed to register user: {e}")
#                 await session.rollback()
#                 raise
#             except Exception as e:
#                 logger.error(f"Unexpected error during registration: {e}")
#                 await session.rollback()
#                 raise
#
#     async def update_user(self, user_id: int, data: UpdateUser, logger: logging.Logger):
#         async with ConnectionManager() as session:
#             try:
#                 # Fetch the existing user
#                 existing_user = await self.fetch_existing_user(session, user_id, logger)
#
#                 if not existing_user:
#                     logger.error(f"User not found: {user_id}")
#                     raise ValueError("User not found.")
#
#                 logger.debug(f"Updating user with data: {data}")
#
#                 # Check user role
#                 current_user_role = existing_user.role.role  # Assuming 'role' is a relationship
#                 if current_user_role == "ADMIN":
#                     # Admins can update the organization
#                     existing_user.organization = self.update_existing_user_organization(existing_user.organization,
#                                                                                    data.organization)
#                     logger.debug(f"Updated organization for user: {user_id}")
#
#                 # Update the existing user with data from DTO
#                 existing_user = self.update_existing_user(existing_user.address, existing_user, data, logger)
#
#                 # Commit the changes to the database
#                 session.add_all([existing_user.address, existing_user.organization, existing_user])
#
#                 # Commit all changes
#                 await session.commit()
#
#                 logger.info(f"User updated successfully: {existing_user}")
#                 return await self.entity_to_dto(existing_user, logger)
#
#             except SQLAlchemyError as e:
#                 logger.error(f"Failed to update user: {e}")
#                 await session.rollback()
#                 raise
#             except Exception as e:
#                 logger.error(f"Unexpected error during user update: {e}")
#                 await session.rollback()
#                 raise
#
#     @staticmethod
#     def update_existing_user_organization(organization_entity, org_data) -> OrganizationEntity:
#         """Convert organization DTO to entity."""
#         organization_entity.organization_name = org_data.organization_name
#         organization_entity.display_name = org_data.display_name
#         organization_entity.gstin = org_data.gstin
#         organization_entity.pan = org_data.pan
#         organization_entity.tan = org_data.tan
#         organization_entity.organization_type = org_data.organization_type
#         organization_entity.incorporation_date = org_data.incorporation_date
#         organization_entity.cin = org_data.cin
#
#         return organization_entity
#
#     @staticmethod
#     def update_existing_user(existing_address: AddressEntity, existing_user: UserEntity, data: UpdateUser,
#                              logger) -> UserEntity:
#         """Convert Pydantic model to SQLAlchemy model."""
#         try:
#             logger.debug(f"Converting DTO to entity for user: {data.first_name} {data.last_name}")
#
#             existing_address.address_line_1 = data.address.address_line_1
#             existing_address.address_line_2 = data.address.address_line_2
#             existing_address.city = data.address.city
#             existing_address.state = data.address.state
#             existing_address.country = data.address.country
#             existing_address.pincode = data.address.pincode
#
#             existing_user.first_name = data.first_name
#             existing_user.last_name = data.last_name
#             existing_user.mobile_no = data.mobile_no
#             existing_user.address = existing_address
#
#             logger.debug(f"Converted DTO to entity: {existing_user}")
#             return existing_user
#         except Exception as e:
#             logger.error(f"Error converting DTO to entity: {e}")
#             raise
#
#     async def get_by_id(self, user_id: int, logger: logging.Logger):
#         async with ConnectionManager() as session:
#             try:
#                 logger.info(f"Fetching user by ID: {user_id}")
#                 user = await self.fetch_existing_user(session, user_id, logger)
#
#                 if user:
#                     logger.info(f"User found with ID: {user_id}")
#                     return await self.entity_to_dto(user, logger)
#                 else:
#                     logger.warning(f"No user found with ID: {user_id}")
#                     return None
#             except SQLAlchemyError as e:
#                 logger.error(f"Failed to fetch user by ID: {user_id}, error: {e}")
#                 raise
#             except Exception as e:
#                 logger.error(f"Unexpected error during get_by_id for user_id: {user_id}: {e}")
#                 raise
#
#     async def get_by_username(self, username: str, logger: logging.Logger):
#         async with ConnectionManager() as session:
#             try:
#                 logger.info(f"Fetching user by username: {username}")
#                 user = await self.fetch_existing_user_by_username(session, username, logger)
#
#                 if user:
#                     logger.info(f"User found with username: {username}")
#                     return await self.entity_to_dto(user, logger)
#                 else:
#                     logger.warning(f"No user found with username: {username}")
#                     return None
#             except SQLAlchemyError as e:
#                 logger.error(f"Failed to fetch user by username: {username}, error: {e}")
#                 raise
#             except Exception as e:
#                 logger.error(f"Unexpected error during get_by_username for username: {username}: {e}")
#                 raise
#
#     async def get_by_role_id(self, role_id: int, logger: logging.Logger):
#         async with ConnectionManager() as session:
#             try:
#                 logger.info(f"Fetching users by role ID: {role_id}")
#                 users = await self.fetch_users_by_role_id(session, role_id, logger)
#
#                 if users:
#                     logger.info(f"Users found with role ID: {role_id}")
#                     return [await self.entity_to_dto(user, logger) for user in users]
#                 else:
#                     logger.warning(f"No users found with role ID: {role_id}")
#                     return []
#             except SQLAlchemyError as e:
#                 logger.error(f"Failed to fetch users by role ID: {role_id}, error: {e}")
#                 raise
#             except Exception as e:
#                 logger.error(f"Unexpected error during get_by_role_id for role_id: {role_id}: {e}")
#                 raise
#
#     async def get_all(self, logger: logging.Logger, page: int, size: int, search_key: Optional[str] = None):
#         async with ConnectionManager() as session:
#             try:
#                 logger.info(f"Fetching users with pagination - page: {page}, size: {size}, searchKey: {search_key}")
#
#                 query = select(UserEntity).options(
#                     selectinload(UserEntity.address),
#                     selectinload(UserEntity.organization)
#                     .selectinload(OrganizationEntity.organization_subscription)  # Eager load organization_subscription
#                     .selectinload(OrganizationSubscriptionEntity.subscription)
#                     .selectinload(SubscriptionEntity.services)
#                     .selectinload(ServiceEntity.api_permissions),
#                     selectinload(UserEntity.role),
#                     selectinload(UserEntity.login),
#                     selectinload(UserEntity.permission)
#                 )
#
#                 if search_key:
#                     query = query.join(UserEntity.organization) \
#                         .join(UserEntity.address) \
#                         .where(or_(
#                         UserEntity.first_name.ilike(f"%{search_key}%"),
#                         UserEntity.last_name.ilike(f"%{search_key}%"),
#                         UserEntity.email_id.ilike(f"%{search_key}%"),
#                         UserEntity.mobile_no.ilike(f"%{search_key}%"),
#                         AddressEntity.address_line_1.ilike(f"%{search_key}%"),
#                         AddressEntity.address_line_2.ilike(f"%{search_key}%"),
#                         AddressEntity.city.ilike(f"%{search_key}%"),
#                         AddressEntity.state.ilike(f"%{search_key}%"),
#                         AddressEntity.country.ilike(f"%{search_key}%"),
#                         AddressEntity.pincode.ilike(f"%{search_key}%"),
#                         OrganizationEntity.organization_name.ilike(f"%{search_key}%"),
#                         OrganizationEntity.display_name.ilike(f"%{search_key}%"),
#                         OrganizationEntity.gstin.ilike(f"%{search_key}%"),
#                         OrganizationEntity.pan.ilike(f"%{search_key}%"),
#                         OrganizationEntity.tan.ilike(f"%{search_key}%"),
#                         OrganizationEntity.organization_type.ilike(f"%{search_key}%"),
#                         OrganizationEntity.cin.ilike(f"%{search_key}%"),
#                         OrganizationEntity.incorporation_date.cast(String).ilike(f"%{search_key}%")
#                     ))
#
#                 # Fetch total count of filtered users
#                 total_elements = await session.execute(select(func.count()).select_from(query.subquery()))
#                 total_elements = total_elements.scalar()
#
#                 # Apply pagination and execute query
#                 result = await session.execute(
#                     query.offset((page - 1) * size).limit(size)
#                 )
#                 users = result.scalars().all()
#
#                 if users:
#                     logger.info(f"{len(users)} users found on page {page}")
#                     users_dto = [await self.entity_to_dto(user, logger) for user in users]
#
#                     # Returning paginated data
#                     return {
#                         "data": users_dto,
#                         "total_pages": (total_elements // size) + (1 if total_elements % size > 0 else 0),
#                         "total_elements": total_elements
#                     }
#                 else:
#                     logger.warning("No users found")
#                     return {
#                         "data": [],
#                         "total_pages": 0,
#                         "total_elements": 0
#                     }
#
#             except SQLAlchemyError as e:
#                 logger.error(f"Failed to fetch users, error: {e}")
#                 raise
#             except Exception as e:
#                 logger.error(f"Unexpected error during get_all: {e}")
#                 raise
#
#     async def delete_user(self, user_id: int, logger: logging.Logger):
#         async with ConnectionManager() as session:
#             try:
#                 logger.debug(f"Deleting user with ID: {user_id}")
#
#                 # Find the user by ID
#                 result = await session.execute(
#                     select(UserEntity)
#                     .options(
#                         selectinload(UserEntity.address),
#                         selectinload(UserEntity.organization).selectinload(
#                             OrganizationEntity.organization_subscription),
#                         selectinload(UserEntity.login),
#                         selectinload(UserEntity.permission)
#                     )  # Eager loading
#                     .filter(UserEntity.id == user_id)
#                 )
#                 user_to_delete = result.scalars().first()
#
#                 if user_to_delete is None:
#                     logger.warning(f"User with ID {user_id} not found.")
#                     return {"message": "User not found"}, 404  # Return a not found response
#
#                 # If user exists, delete the login entity first (if necessary)
#                 if user_to_delete.login:
#                     logger.debug(f"Deleting login entity for user ID: {user_id}")
#                     await session.delete(user_to_delete.login)
#
#                 if user_to_delete.address:
#                     logger.debug(f"Deleting address entity for user ID: {user_id}")
#                     await session.delete(user_to_delete.address)
#
#                 # Check if the user has an associated permission entity
#                 if user_to_delete.permission:
#                     logger.debug(f"Deleting permission entity for user ID: {user_id}")
#                     await session.delete(user_to_delete.permission)
#
#                 # Check if the user is the only one in the organization
#                 if await self.is_organization_mapped_to_multiple_users(session, user_to_delete.organization_id, logger):
#                     user_to_delete.organization = None
#                     logger.debug(f"User ID: {user_id} is unlinked from organization")
#                 else:
#                     # If no other users are linked to the organization, delete the organization subscription if it exists
#                     if user_to_delete.organization.organization_subscription:
#                         logger.debug(
#                             f"Deleting organization subscription for organization ID: {user_to_delete.organization_id}")
#                         await session.delete(user_to_delete.organization.subscription)
#                     logger.debug(f"Deleting organization entity for organization ID: {user_to_delete.organization_id}")
#                     await session.delete(user_to_delete.organization)
#
#                 # Delete the user entity
#                 logger.debug(f"Deleting user entity with ID: {user_id}")
#                 await session.delete(user_to_delete)
#
#                 # Commit the changes
#                 await session.commit()
#                 logger.info(f"User with ID {user_id} deleted successfully.")
#                 return {"message": "User deleted successfully"}, 200  # Return a success response
#
#             except SQLAlchemyError as e:
#                 logger.error(f"Failed to delete user ID {user_id}: {e}")
#                 await session.rollback()
#                 raise
#             except Exception as e:
#                 logger.error(f"Unexpected error during user deletion for ID {user_id}: {e}")
#                 await session.rollback()
#                 raise
#
#     async def create_login(self, user: UserEntity, logger: logging.Logger):
#         try:
#             # Set login details
#             logger.debug(f"Entering create_login method: {user.email_id}")
#
#             # Create an instance of LoginEntity
#             login_entity = LoginEntity()
#             login_entity.username = user.email_id
#
#             # Generate password and set login details
#             password = self.generate_strong_password()
#             login_entity.password = password
#             login_entity.account_active = True
#
#             logger.info(f"Created login entity for user: {user.email_id}")
#             return login_entity
#         except Exception as e:
#             logger.error(f"Error during login creation: {e}")
#             raise
#
#     @staticmethod
#     def organization_dto_to_entity(org_data, subscription_data) -> OrganizationEntity:
#         """Convert organization DTO to entity."""
#         organization_entity = OrganizationEntity(
#             organization_name=org_data.organization_name,
#             display_name=org_data.display_name,
#             gstin=org_data.gstin,
#             pan=org_data.pan,
#             tan=org_data.tan,
#             organization_type=org_data.organization_type,
#             incorporation_date=org_data.incorporation_date,
#             cin=org_data.cin
#         )
#
#         # If subscription data is provided, create an OrganizationSubscriptionEntity
#         if subscription_data is not None:
#             organization_subscription = OrganizationSubscriptionEntity(
#                 subscription_date=date.today(),  # Set the current date for subscription_date
#                 subscription=subscription_data
#             )
#             organization_entity.organization_subscription = organization_subscription
#
#         return organization_entity
#
#     @staticmethod
#     def dto_to_entity(data: Union[Register, CreateUser], logger) -> UserEntity:
#         """Convert Pydantic model to SQLAlchemy model."""
#         try:
#             logger.debug(f"Converting DTO to entity for user: {data.first_name} {data.last_name}")
#
#             address = AddressEntity(
#                 address_line_1=data.address.address_line_1,
#                 address_line_2=data.address.address_line_2,
#                 city=data.address.city,
#                 state=data.address.state,
#                 country=data.address.country,
#                 pincode=data.address.pincode
#             )
#
#             new_user = UserEntity(
#                 first_name=data.first_name,
#                 last_name=data.last_name,
#                 email_id=data.email_id,
#                 mobile_no=data.mobile_no,
#                 address=address
#             )
#
#             logger.debug(f"Converted DTO to entity: {new_user}")
#             return new_user
#         except Exception as e:
#             logger.error(f"Error converting DTO to entity: {e}")
#             raise
#
#     @staticmethod
#     async def entity_to_dto(user: UserEntity, logger) -> UserDTO:
#         """Convert UserEntity to UserDTO."""
#         logger.debug("Starting conversion of UserEntity to UserDTO for user id: %s", user.id)
#
#         # Mapping AddressEntity to AddressDTO
#         address_dto = AddressDTO(
#             id=user.address.id if user.address else None,
#             address_line_1=user.address.address_line_1 if user.address else None,
#             address_line_2=user.address.address_line_2 if user.address else None,
#             city=user.address.city if user.address else None,
#             state=user.address.state if user.address else None,
#             country=user.address.country if user.address else None,
#             pincode=user.address.pincode if user.address else None,
#             reference_id=user.address.reference_id if user.address else None
#         )
#         logger.debug("Mapped AddressEntity to AddressDTO: %s", address_dto)
#
#         # Mapping OrganizationSubscriptionEntity to OrganizationSubscriptionDTO
#         if user.organization and user.organization.organization_subscription:
#             org_sub = user.organization.organization_subscription  # Assuming it's now a single object
#
#             subscription_dto = SubscriptionDTO(
#                 id=org_sub.subscription.id if org_sub.subscription else None,
#                 name=org_sub.subscription.name if org_sub.subscription else None,
#                 validity=org_sub.subscription.validity,
#                 cost=org_sub.subscription.cost,
#                 active_status=org_sub.subscription.active_status,
#                 subscription_type=org_sub.subscription.subscription_type.name if org_sub.subscription.subscription_type else None,
#                 services=[ServiceDTO(
#                     id=service.id,
#                     name=service.name,
#                     description=service.description,
#                     active_status=service.active_status,
#                     api_permissions=[
#                         ApiPermissionDTO(
#                             id=api_permission.id,
#                             name=api_permission.name,
#                             method=api_permission.method,
#                             api_url=api_permission.api_url,
#                             description=api_permission.description,
#                             status=api_permission.status
#                         )
#                         for api_permission in service.api_permissions
#                     ] if service.api_permissions else None
#                 ) for service in org_sub.subscription.services] if org_sub.subscription.services else None,
#             )
#             logger.debug("Mapped OrganizationSubscriptionEntity to SubscriptionDTO: %s", subscription_dto)
#
#             organization_subscription_dto = OrganizationSubscriptionDTO(
#                 id=org_sub.id,
#                 subscription_date=org_sub.subscription_date,
#                 subscription=subscription_dto
#             )
#
#             organization_dto = OrganizationDTO(
#                 id=user.organization.id,
#                 organization_name=user.organization.organization_name,
#                 display_name=user.organization.display_name,
#                 gstin=user.organization.gstin,
#                 pan=user.organization.pan,
#                 tan=user.organization.tan,
#                 organization_type=user.organization.organization_type,
#                 incorporation_date=user.organization.incorporation_date,
#                 cin=user.organization.cin,
#                 organization_subscription=organization_subscription_dto
#             )
#             logger.debug("Mapped OrganizationEntity to OrganizationDTO: %s", organization_dto)
#         else:
#             organization_dto = None
#
#         # Mapping LoginEntity to LoginDTO
#         login_dto = None
#         if user.login:
#             login_dto = LoginDTO(
#                 id=user.login.id,
#                 username=user.login.username,
#                 password=None,  # Don't expose password for security
#                 account_active=user.login.account_active,
#                 account_inactive_reason=user.login.account_inactive_reason,
#                 login_time=user.login.login_time,
#                 logout_time=user.login.logout_time,
#             )
#             logger.debug("Mapped LoginEntity to LoginDTO: %s", login_dto)
#
#         # Mapping RoleEntity to RoleDTO
#         role_dto = None
#         if user.role:
#             role_dto = RoleDTO(
#                 id=user.role.id,
#                 role=user.role.role,
#                 description=user.role.description,
#             )
#             logger.debug("Mapped RoleEntity to RoleDTO: %s", role_dto)
#
#         # Mapping PermissionEntity to PermissionDTO
#         permission_dto = None
#         if user.permission:
#             permission = user.permission
#             permission_dto = UserPermission(
#                 id=permission.id,
#                 name=permission.name,
#                 permission=json.loads(permission.permission) if permission.permission else {}
#             )
#             logger.debug("Mapped PermissionEntity to PermissionDTO: %s", permission_dto)
#
#         # Creating UserDTO from the above mappings
#         user_dto = UserDTO(
#             id=user.id,
#             customer_id=user.customer_id,
#             first_name=user.first_name,
#             last_name=user.last_name,
#             email_id=user.email_id,
#             mobile_no=user.mobile_no,
#             address=address_dto,
#             organization=organization_dto,
#             login=login_dto,
#             role=role_dto,
#             permission=permission_dto
#         )
#         logger.debug("Successfully created UserDTO: %s", user_dto)
#
#         return user_dto
#
#
#
