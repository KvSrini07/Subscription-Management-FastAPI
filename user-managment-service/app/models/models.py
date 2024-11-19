from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Date, Enum, JSON
from sqlalchemy.orm import relationship
import enum
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class SubscriptionType(str, enum.Enum):
    DAYS = "DAYS"
    MONTH = "MONTH"
    YEAR = "YEAR"

class HttpMethod(str, enum.Enum):
    POST = "POST"
    PUT = "PUT"
    GET = "GET"
    DELETE = "DELETE"

class SubscriptionEntity(Base):
    __tablename__ = "subscription"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    validity = Column(Integer, nullable=True)
    cost = Column(Integer, nullable=True)
    active_status = Column(Boolean, nullable=True)
    subscription_type = Column(Enum(SubscriptionType), nullable=True)

    # services = relationship("ServiceEntity", secondary="subscription_services_mapping", back_populates="subscriptions")
    services = relationship("ServiceEntity", secondary="subscription_services_mapping",
                            back_populates="subscriptions")
# Service Entity
class ServiceEntity(Base):
    __tablename__ = "subscription_service"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    active_status = Column(Boolean, nullable=True)

    subscriptions = relationship("SubscriptionEntity", secondary="subscription_services_mapping", back_populates="services")

    # Relationship to ApiPermissionEntity via the service_api_permissions_mapping table
    api_permissions = relationship(
        "ApiPermissionEntity",
        secondary="service_api_permissions_mapping",
        back_populates="services"
    )
    page_permissions = relationship(
        "PagePermissionEntity",
        secondary="service_api_page_permissions_mapping",
        back_populates="services"
    )

# Mapping Table for Subscription and Service
class SubscriptionServicesMapping(Base):
    __tablename__ = "subscription_services_mapping"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subscription_id = Column(Integer, ForeignKey('subscription.id'))
    service_id = Column(Integer, ForeignKey('subscription_service.id'))

# ApiPermission Entity
class ApiPermissionEntity(Base):
    __tablename__ = "api_permission"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    # method = Column(String(10), nullable=True)  # Store HTTP Method as string
    method = Column(Enum(HttpMethod), nullable=True)
    api_url = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)
    status = Column(Boolean, nullable=True)

    # Relationship to ServiceEntity via the service_api_permissions_mapping table
    services = relationship(
        "ServiceEntity",
        secondary="service_api_permissions_mapping",
        back_populates="api_permissions"
    )


# Mapping Table for Service and ApiPermission
class ServiceApiPermissionsMapping(Base):
    __tablename__ = 'service_api_permissions_mapping'

    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey('subscription_service.id'))
    api_permission_id = Column(Integer, ForeignKey('api_permission.id'))

    # Define relationships between the entities
    service_entity = relationship("ServiceEntity", backref="api_permissions_mappings")
    api_permission_entity = relationship("ApiPermissionEntity", backref="service_permissions_mappings")


# PagePermissionEntity
class PagePermissionEntity(Base):
    __tablename__ = "page_permission"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(String(512))
    status = Column(Boolean, default=True)
    page_url = Column(String(512), nullable=False)

    # Relationship to ApiPermissionEntity
    services = relationship(
        "ServiceEntity",
        secondary="service_api_page_permissions_mapping",
        back_populates="page_permissions"
    )

class ServiceApiPagePermissionsMapping(Base):
    __tablename__ = "service_api_page_permissions_mapping"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_id = Column(Integer, ForeignKey('subscription_service.id'))
    page_permission_id = Column(Integer, ForeignKey('page_permission.id'))

    # Establishing relationships with entities
    service_entity = relationship("ServiceEntity")
    page_permission_entity = relationship("PagePermissionEntity")




class RoleEntity(Base):
    __tablename__ = 'role'

    id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(String(100), unique=True, nullable=False)
    description = Column(String(512))

    # Back-reference to UserEntity
    users = relationship("UserEntity", back_populates="role")



class LoginEntity(Base):
    __tablename__ = 'login'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True)
    password = Column(String(255))
    account_active = Column(Boolean)
    account_inactive_reason = Column(String(512))
    login_time = Column(DateTime)
    logout_time = Column(DateTime)

    # Establish back-reference to UserEntity
    user = relationship("UserEntity", back_populates="login")  # Add this line


class AddressEntity(Base):
    __tablename__ = 'address'

    id = Column(Integer, primary_key=True, autoincrement=True)
    address_line_1 = Column(String(255))
    address_line_2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    pincode = Column(String(20))
    reference_id = Column(String(255))


class OrganizationSubscriptionEntity(Base):
    __tablename__ = 'organization_subscription_details'

    id = Column(Integer, primary_key=True, autoincrement=True)
    subscription_date = Column(Date)
    subscription_id = Column(Integer, ForeignKey('subscription.id'))
    organization_id = Column(Integer, ForeignKey('organization.id'), unique=True)  # Unique constraint added

    subscription = relationship("SubscriptionEntity")
    organization = relationship("OrganizationEntity", back_populates="organization_subscription")  # Update relationship


class OrganizationEntity(Base):
    __tablename__ = 'organization'

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_name = Column(String(255))
    display_name = Column(String(255))
    gstin = Column(String(15), unique=True, nullable=False)
    pan = Column(String(10), unique=True, nullable=False)
    tan = Column(String(10), unique=True, nullable=False)
    organization_type = Column(String(100))
    incorporation_date = Column(Date)
    cin = Column(String(21), unique=True, nullable=False)

    # relationship
    users = relationship("UserEntity", back_populates="organization")
    organization_subscription = relationship("OrganizationSubscriptionEntity", back_populates="organization", uselist=False)  # Set uselist to False


class UserEntity(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(50))
    first_name = Column(String(100))
    last_name = Column(String(100))
    email_id = Column(String(255), unique=True, nullable=False)
    mobile_no = Column(String(15), unique=True, nullable=False)

    login_id = Column(Integer, ForeignKey('login.id'))
    role_id = Column(Integer, ForeignKey('role.id'))
    organization_id = Column(Integer, ForeignKey('organization.id'))
    # Removed permission_id as it will be handled in PermissionEntity now
    address_id = Column(Integer, ForeignKey('address.id'))

    login = relationship("LoginEntity", back_populates="user")
    role = relationship("RoleEntity", back_populates="users")
    organization = relationship("OrganizationEntity", back_populates="users")
    address = relationship("AddressEntity")

    # Establishing one-to-one relationship with PermissionEntity
    permission = relationship("PermissionEntity", back_populates="user", uselist=False)


class PermissionEntity(Base):
    __tablename__ = 'permission'

    id = Column(Integer, primary_key=True, autoincrement=True)
    permission_name = Column(String(255), unique=True, nullable=False)
    permission = Column(JSON)

    user_id = Column(Integer, ForeignKey('user.id'))

    # Establishing back-reference with user
    user = relationship("UserEntity", back_populates="permission", foreign_keys=[user_id], uselist=False)



# class ApiPermissionEntity(Base):
#     tablename = 'api_permission'
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     name = Column(String(255), unique=True, nullable=False)
#     method = Column(Enum(HttpMethod))
#     api_url = Column(String(512))
#     description = Column(String(512))
#     status = Column(Boolean)
#
#     # This establishes a back reference for the services related to this API permission.
#     services = relationship("ServiceApiPermissionsMapping", back_populates="api_permission_entity")
#
#
# class ServiceEntity(Base):
#     tablename = 'subscription_service'
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     name = Column(String(255), unique=True, nullable=False)
#     description = Column(String(512))
#     active_status = Column(Boolean)
#
#     # These are back references for the subscriptions and API permissions related to this service.
#     subscription_entities = relationship("SubscriptionServicesMapping", back_populates="service_entity")
#     permission_entities = relationship("ServiceApiPagePermissionsMapping", back_populates="service_entity")
#

# class PagePermissionEntity(Base):
#     tablename = 'page_permission'
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     name = Column(String(255), unique=True, nullable=False)
#     description = Column(String(512))
#     status = Column(Boolean, default=True)  # Default status can be True
#     page_url = Column(String(512), nullable=False)  # URL of the page
#
#
# class ServiceApiPagePermissionsMapping(Base):
#     tablename = 'service_api_page_permissions_mapping'
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     service_id = Column(Integer, ForeignKey('subscription_service.id'))
#     api_permission_id = Column(Integer, ForeignKey('api_permission.id'))
#     page_permission_id = Column(Integer, ForeignKey('page_permission.id'))  # Adding page_permission_id
#
#     # Establishing relationships to the related entities with appropriate back_populates
#     service_entity = relationship("ServiceEntity", back_populates="api_permission_entities")
#     api_permission_entity = relationship("ApiPermissionEntity", back_populates="services")
#     page_permission_entity = relationship("PagePermissionEntity")  # Relationship to PagePermissionEntity






#Uv Code
# from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, DateTime, Date, Enum, JSON
# from sqlalchemy.orm import relationship
# import enum
# from sqlalchemy.ext.declarative import declarative_base
#
# Base = declarative_base()
#
# class SubscriptionType(str, enum.Enum):
#     DAYS = "DAYS"
#     MONTH = "MONTH"
#     YEAR = "YEAR"
#
# class HttpMethod(str, enum.Enum):
#     POST = "POST"
#     PUT = "PUT"
#     GET = "GET"
#     DELETE = "DELETE"
#
# class SubscriptionEntity(Base):
#     __tablename__ = "subscription"
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     name = Column(String(255), unique=True, nullable=False)
#     validity = Column(Integer, nullable=True)
#     cost = Column(Integer, nullable=True)
#     active_status = Column(Boolean, nullable=True)
#     subscription_type = Column(Enum(SubscriptionType), nullable=True)
#
#     # services = relationship("ServiceEntity", secondary="subscription_services_mapping", back_populates="subscriptions")
#     services = relationship("ServiceEntity", secondary="subscription_services_mapping",
#                             back_populates="subscriptions")
# # Service Entity
# class ServiceEntity(Base):
#     __tablename__ = "subscription_service"
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     name = Column(String(255), unique=True, nullable=False)
#     description = Column(String(255), nullable=True)
#     active_status = Column(Boolean, nullable=True)
#
#     subscriptions = relationship("SubscriptionEntity", secondary="subscription_services_mapping", back_populates="services")
#
#     # Relationship to ApiPermissionEntity via the service_api_permissions_mapping table
#     api_permissions = relationship(
#         "ApiPermissionEntity",
#         secondary="service_api_permissions_mapping",
#         back_populates="services"
#     )
#
# # Mapping Table for Subscription and Service
# class SubscriptionServicesMapping(Base):
#     __tablename__ = "subscription_services_mapping"
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     subscription_id = Column(Integer, ForeignKey('subscription.id'))
#     service_id = Column(Integer, ForeignKey('subscription_service.id'))
#
# # ApiPermission Entity
# class ApiPermissionEntity(Base):
#     __tablename__ = "api_permission"
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     name = Column(String(255), unique=True, nullable=False)
#     # method = Column(String(10), nullable=True)  # Store HTTP Method as string
#     method = Column(Enum(HttpMethod), nullable=True)
#     api_url = Column(String(255), nullable=True)
#     description = Column(String(255), nullable=True)
#     status = Column(Boolean, nullable=True)
#
#     # Relationship to ServiceEntity via the service_api_permissions_mapping table
#     services = relationship(
#         "ServiceEntity",
#         secondary="service_api_permissions_mapping",
#         back_populates="api_permissions"
#     )
#
# # Mapping Table for Service and ApiPermission
# class ServiceApiPermissionsMapping(Base):
#     __tablename__ = 'service_api_permissions_mapping'
#
#     id = Column(Integer, primary_key=True)
#     service_id = Column(Integer, ForeignKey('subscription_service.id'))
#     api_permission_id = Column(Integer, ForeignKey('api_permission.id'))
#
#     # Define relationships between the entities
#     service_entity = relationship("ServiceEntity", backref="api_permissions_mappings")
#     api_permission_entity = relationship("ApiPermissionEntity", backref="service_permissions_mappings")
#
#
#
# class RoleEntity(Base):
#     __tablename__ = 'role'
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     role = Column(String(100), unique=True, nullable=False)
#     description = Column(String(512))
#
#     # Back-reference to UserEntity
#     users = relationship("UserEntity", back_populates="role")
#
#
# class LoginEntity(Base):
#     __tablename__ = 'login'
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     username = Column(String(100), unique=True)
#     password = Column(String(255))
#     account_active = Column(Boolean)
#     account_inactive_reason = Column(String(512))
#     login_time = Column(DateTime)
#     logout_time = Column(DateTime)
#
#     # Establish back-reference to UserEntity
#     user = relationship("UserEntity", back_populates="login")  # Add this line
#
#
# class AddressEntity(Base):
#     __tablename__ = 'address'
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     address_line_1 = Column(String(255))
#     address_line_2 = Column(String(255))
#     city = Column(String(100))
#     state = Column(String(100))
#     country = Column(String(100))
#     pincode = Column(String(20))
#     reference_id = Column(String(255))
#
#
# class OrganizationSubscriptionEntity(Base):
#     __tablename__ = 'organization_subscription_details'
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     subscription_date = Column(Date)
#     subscription_id = Column(Integer, ForeignKey('subscription.id'))
#     organization_id = Column(Integer, ForeignKey('organization.id'), unique=True)  # Unique constraint added
#
#     subscription = relationship("SubscriptionEntity")
#     organization = relationship("OrganizationEntity", back_populates="organization_subscription")  # Update relationship
#
#
# class OrganizationEntity(Base):
#     __tablename__ = 'organization'
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     organization_name = Column(String(255))
#     display_name = Column(String(255))
#     gstin = Column(String(15), unique=True, nullable=False)
#     pan = Column(String(10), unique=True, nullable=False)
#     tan = Column(String(10), unique=True, nullable=False)
#     organization_type = Column(String(100))
#     incorporation_date = Column(Date)
#     cin = Column(String(21), unique=True, nullable=False)
#
#     # relationship
#     users = relationship("UserEntity", back_populates="organization")
#     organization_subscription = relationship("OrganizationSubscriptionEntity", back_populates="organization", uselist=False)  # Set uselist to False
#
#
# class UserEntity(Base):
#     __tablename__ = 'user'
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     customer_id = Column(String(50))
#     first_name = Column(String(100))
#     last_name = Column(String(100))
#     email_id = Column(String(255), unique=True, nullable=False)
#     mobile_no = Column(String(15), unique=True, nullable=False)
#
#     login_id = Column(Integer, ForeignKey('login.id'))
#     role_id = Column(Integer, ForeignKey('role.id'))
#     organization_id = Column(Integer, ForeignKey('organization.id'))
#     # Removed permission_id as it will be handled in PermissionEntity now
#     address_id = Column(Integer, ForeignKey('address.id'))
#
#     login = relationship("LoginEntity", back_populates="user")
#     role = relationship("RoleEntity", back_populates="users")
#     organization = relationship("OrganizationEntity", back_populates="users")
#     address = relationship("AddressEntity")
#
#     # Establishing one-to-one relationship with PermissionEntity
#     permission = relationship("PermissionEntity", back_populates="user", uselist=False)
#
#
# class PermissionEntity(Base):
#     __tablename__ = 'permission'
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     name = Column(String(255), nullable=False)
#     permission = Column(JSON)
#
#     user_id = Column(Integer, ForeignKey('user.id'))
#
#     # Establishing back-reference with user
#     user = relationship("UserEntity", back_populates="permission", foreign_keys=[user_id], uselist=False)
#
