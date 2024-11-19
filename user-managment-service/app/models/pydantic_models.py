from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime, date
from app.models.models import SubscriptionType, HttpMethod

# Create
class CreateSubscription(BaseModel):
    name: str
    validity: int
    cost: float
    active_status: bool
    subscription_type: SubscriptionType

    @validator('cost')
    def validate_cost(cls, value):
        if value <= 0:
            raise ValueError('Cost must be greater than zero.')
        return value

    class Config:
        orm_mode = True

class CreateService(BaseModel):
    name: str
    description: Optional[str] = None
    active_status: bool
    api_permission_id: Optional[List[int]]=None
    subscription_id: int

    class Config:
        orm_mode = True


class CreateApiPermission(BaseModel):
    name: str
    method: HttpMethod
    api_url: str
    description: Optional[str] = None
    status: bool

    class Config:
        orm_mode = True

class CreateSubscriptionServiceMapping(BaseModel):
    subscription_id: int
    service_id: List[int]

    class Config:
        orm_mode = True

class CreateServiceApiPermissionMapping(BaseModel):
    service_id: int
    api_permission_id: List[int]

    class Config:
        orm_mode = True


class PagePermissionCreateDTO(BaseModel):
    name: str
    description: Optional[str] = None
    status: bool = True
    page_url: str

    class Config:
        orm_mode = True


class ServiceApiPagePermissionsMappingCreateDTO(BaseModel):
    service_id: int
    page_permission_id: List[int]

    class Config:
        orm_mode = True

class CreateRole(BaseModel):
    role: str
    description: Optional[str] = None

    class Config:
        orm_mode = True


class CreateAddress(BaseModel):
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None

    class Config:
        orm_mode = True


class CreateOrganization(BaseModel):
    organization_name: str
    display_name: str
    gstin: str
    pan: str
    tan: str
    organization_type: Optional[str] = None
    incorporation_date: Optional[str] = None  # Store as string but validate as date
    cin: str

    @validator('incorporation_date', pre=True, always=True)
    def parse_incorporation_date(cls, value):
        if value:
            return str(value)  # Or add any custom behavior to convert date to string
        return value

    class Config:
        json_encoders = {
            date: lambda v: v.strftime('%Y-%m-%d')  # Define custom serialization for date
        }


# class CreatePermission(BaseModel):
#     permission_name: str
#     permission: dict  # You can use a more specific type if known.
#     user_id: int
#
#     class Config:
#         orm_mode = True

class UpdatePermission(BaseModel):
    name: str
    permission: Optional[str] = None

    class Config:
        orm_mode = True


class Register(BaseModel):
    first_name: str
    last_name: str
    email_id: str
    mobile_no: str
    subscription_id: int
    address: CreateAddress
    organization: CreateOrganization

    class Config:
        orm_mode = True

class CreateUser(BaseModel):
    first_name: str
    last_name: str
    email_id: str
    mobile_no: str
    address: CreateAddress
    admin_id: int

    class Config:
        orm_mode = True

class UpdateUser(BaseModel):
    first_name: str
    last_name: str
    mobile_no: str
    address: CreateAddress
    organization: CreateOrganization

    class Config:
        orm_mode = True


# DTO
class PagePermissionDTO(BaseModel):
    id: Optional[int]
    name: str
    description: Optional[str] = None
    status: bool = True
    page_url: str

    class Config:
        orm_mode = True

class ServiceApiPagePermissionsMappingDTO(BaseModel):
    id: Optional[int]
    service_id: int
    page_permission_id: List[int]

    class Config:
        orm_mode = True


class ApiPermissionDTO(BaseModel):
    id: int
    name: str
    method: HttpMethod
    api_url: str
    description: Optional[str] = None
    status: bool

    class Config:
        orm_mode = True


class ServiceDTO(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    active_status: bool
    api_permissions: Optional[List[ApiPermissionDTO]]=None
    page_permissions: Optional[List[PagePermissionDTO]] = None

    class Config:
        orm_mode = True


class SubscriptionDTO(BaseModel):
    id: int
    name: str
    validity: int
    cost: float
    active_status: bool
    subscription_type: SubscriptionType
    services: Optional[List[ServiceDTO]] = None

    @validator('cost')
    def validate_cost(cls, value):
        if value <= 0:
            raise ValueError('Cost must be greater than zero.')
        return value

    class Config:
        orm_mode = True

class RoleDTO(BaseModel):
    id: int
    role: str
    description: Optional[str] = None

    class Config:
        orm_mode = True

class LoginDTO(BaseModel):
    id: int
    username: str
    password: Optional[str] = None  # You may want to exclude this for security reasons.
    account_active: bool
    account_inactive_reason: Optional[str] = None
    login_time: Optional[datetime] = None
    logout_time: Optional[datetime] = None

    class Config:
        orm_mode = True


class AddressDTO(BaseModel):
    id: int
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    reference_id: Optional[str] = None

    class Config:
        orm_mode = True


class OrganizationSubscriptionDTO(BaseModel):
    id: int
    subscription_date: datetime
    subscription: SubscriptionDTO

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d') if v else None
        }


class OrganizationDTO(BaseModel):
    id: int
    organization_name: str
    display_name: str
    gstin: str
    pan: str
    tan: str
    organization_type: Optional[str] = None
    incorporation_date: Optional[datetime] = None
    cin: str
    organization_subscription: Optional[OrganizationSubscriptionDTO] = None

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d') if v else None
        }

class UserPermission(BaseModel):
    id: int
    name: str
    permission: dict

    class Config:
        orm_mode = True

class UserDTO(BaseModel):
    id: Optional[int] = None
    customer_id: Optional[str] = None
    first_name: str
    last_name: str
    email_id: str
    mobile_no: str
    address: AddressDTO
    organization: OrganizationDTO
    login: Optional[LoginDTO] = None
    role: Optional[RoleDTO] = None
    permission: Optional[UserPermission] = None

    class Config:
        orm_mode = True

class PermissionUser(BaseModel):
    id: Optional[int] = None
    customer_id: Optional[str] = None
    first_name: str
    last_name: str
    email_id: str
    mobile_no: str
    address: AddressDTO
    organization: OrganizationDTO
    login: Optional[LoginDTO] = None
    role: Optional[RoleDTO] = None

    class Config:
        orm_mode = True

class PermissionDTO(BaseModel):
    id: int
    name: str
    permission: dict  # You can use a more specific type if known.
    user:  Optional[PermissionUser] = None

    class Config:
        orm_mode = True






#Uv Code
# from pydantic import BaseModel, validator, Field
# from typing import Optional, List, Any
# from datetime import datetime, date
# import enum
#
# #Response
# class ResponseBO(BaseModel):
#     code: int
#     status: str
#     embedded: Optional[Any] = Field(alias='data')
#     message: str
#
#     class Config:
#         populate_by_name = True
#
# class PageableResponse(BaseModel):
#     code: int
#     status: str
#     page: int
#     size: int
#     embedded: Optional[Any] = Field(alias='data')
#     message: str
#     totalPages: int
#     totalElements: int
#
#     class Config:
#         populate_by_name = True
#
# class StatusConstant:
#     GET = "Retrieved Successfully"
#     GET_LIST = "Records Retrieved Successfully"
#     CREATED = "Created Successfully"
#     UPDATED = "Updated Successfully"
#     DELETED = "Deleted Successfully"
#     EXISTS = "Already Exists"
#     ACCEPTED = "Request Accepted"
#     UPLOADED = "Uploaded Successfully"
#     MERGE = "Merge By Some Users, You Can't Delete!"
#     NO_CONTENT = "No Record Found"
#     BAD_REQUEST = "Bad Request"
#     UNAUTHORIZED = "Unauthorized Access"
#     FORBIDDEN = "Access Forbidden"
#     NOT_FOUND = "Not Found"
#     METHOD_NOT_ALLOWED = "Method Not Allowed"
#     CONFLICT = "Conflict Detected"
#     INTERNAL_SERVER_ERROR = "An Error Occurred"
#     NOT_IMPLEMENTED = "Feature Not Implemented"
#     BAD_GATEWAY = "Bad Gateway"
#     SERVICE_UNAVAILABLE = "Service Unavailable"
#     GATEWAY_TIMEOUT = "Gateway Timeout"
#     UNSUPPORTED_MEDIA_TYPE = "Unsupported File Type"
#
# #Enum
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
# # Create
# class CreateSubscription(BaseModel):
#     name: str
#     validity: int
#     cost: float
#     active_status: bool
#     subscription_type: SubscriptionType
#
#     class Config:
#         orm_mode = True
#
# class CreateService(BaseModel):
#     name: str
#     description: Optional[str] = None
#     active_status: bool
#     api_permission_id: Optional[List[int]] = None
#     subscription_id: int
#
#     class Config:
#         orm_mode = True
#
#
# class CreateApiPermission(BaseModel):
#     name: str
#     method: HttpMethod
#     api_url: str
#     description: Optional[str] = None
#     status: bool
#
#     class Config:
#         orm_mode = True
#
# class CreateSubscriptionServiceMapping(BaseModel):
#     subscription_id: int
#     service_id: List[int]
#
#     class Config:
#         orm_mode = True
#
# class CreateServiceApiPermissionMapping(BaseModel):
#     service_id: int
#     api_permission_id: List[int]
#
#     class Config:
#         orm_mode = True
#
# class CreateRole(BaseModel):
#     role: str
#     description: Optional[str] = None
#
#     class Config:
#         orm_mode = True
#
#
# class CreateAddress(BaseModel):
#     address_line_1: Optional[str] = None
#     address_line_2: Optional[str] = None
#     city: Optional[str] = None
#     state: Optional[str] = None
#     country: Optional[str] = None
#     pincode: Optional[str] = None
#
#     class Config:
#         orm_mode = True
#
#
# class CreateOrganization(BaseModel):
#     organization_name: str
#     display_name: str
#     gstin: str
#     pan: str
#     tan: str
#     organization_type: Optional[str] = None
#     incorporation_date: Optional[str] = None  # Store as string but validate as date
#     cin: str
#
#     @validator('incorporation_date', pre=True, always=True)
#     def parse_incorporation_date(cls, value):
#         if value:
#             return str(value)  # Or add any custom behavior to convert date to string
#         return value
#
#     class Config:
#         json_encoders = {
#             date: lambda v: v.strftime('%Y-%m-%d')  # Define custom serialization for date
#         }
#

# class CreatePermission(BaseModel):
#     permission_name: str
#     permission: dict  # You can use a more specific type if known.
#     user_id: int
#
#     class Config:
#         orm_mode = True
#
# class UpdatePermission(BaseModel):
#     name: str
#     permission: Optional[str] = None
#
#     class Config:
#         orm_mode = True
#
#
# class Register(BaseModel):
#     first_name: str
#     last_name: str
#     email_id: str
#     mobile_no: str
#     subscription_id: int
#     address: CreateAddress
#     organization: CreateOrganization
#
#     class Config:
#         orm_mode = True
#
# class CreateUser(BaseModel):
#     first_name: str
#     last_name: str
#     email_id: str
#     mobile_no: str
#     address: CreateAddress
#     admin_id: int
#
#     class Config:
#         orm_mode = True
#
# class UpdateUser(BaseModel):
#     first_name: str
#     last_name: str
#     mobile_no: str
#     address: CreateAddress
#     organization: CreateOrganization
#
#     class Config:
#         orm_mode = True
#
#
# # DTO
# class ApiPermissionDTO(BaseModel):
#     id: int
#     name: str
#     method: HttpMethod
#     api_url: str
#     description: Optional[str] = None
#     status: bool
#
#     class Config:
#         orm_mode = True
#
#
# class ServiceDTO(BaseModel):
#     id: int
#     name: str
#     description: Optional[str] = None
#     active_status: bool
#     api_permissions: Optional[List[ApiPermissionDTO]]=None
#
#     class Config:
#         orm_mode = True
#
#
# class SubscriptionDTO(BaseModel):
#     id: int
#     name: str
#     validity: int
#     cost: float
#     active_status: bool
#     subscription_type: SubscriptionType
#     services: Optional[List[ServiceDTO]]=None
#
#     class Config:
#         orm_mode = True
#
#
# class SubscriptionServiceMappingDTO(BaseModel):
#     id: int
#     subscription_id: int
#     service_id: int
#
#     class Config:
#         orm_mode = True
#
#
# class ServiceApiPermissionMappingDTO(BaseModel):
#     id: int
#     service_id: int
#     api_permission_id: int
#
#     class Config:
#         orm_mode = True
#
#
# class RoleDTO(BaseModel):
#     id: int
#     role: str
#     description: Optional[str] = None
#
#     class Config:
#         orm_mode = True
#
# class LoginDTO(BaseModel):
#     id: int
#     username: str
#     password: Optional[str] = None  # You may want to exclude this for security reasons.
#     account_active: bool
#     account_inactive_reason: Optional[str] = None
#     login_time: Optional[datetime] = None
#     logout_time: Optional[datetime] = None
#
#     class Config:
#         orm_mode = True
#
#
# class AddressDTO(BaseModel):
#     id: int
#     address_line_1: Optional[str] = None
#     address_line_2: Optional[str] = None
#     city: Optional[str] = None
#     state: Optional[str] = None
#     country: Optional[str] = None
#     pincode: Optional[str] = None
#     reference_id: Optional[str] = None
#
#     class Config:
#         orm_mode = True
#
#
# class OrganizationSubscriptionDTO(BaseModel):
#     id: int
#     subscription_date: datetime
#     subscription: SubscriptionDTO
#
#     class Config:
#         orm_mode = True
#         json_encoders = {
#             datetime: lambda v: v.strftime('%Y-%m-%d') if v else None
#         }
#
#
# class OrganizationDTO(BaseModel):
#     id: int
#     organization_name: str
#     display_name: str
#     gstin: str
#     pan: str
#     tan: str
#     organization_type: Optional[str] = None
#     incorporation_date: Optional[datetime] = None
#     cin: str
#     organization_subscription: Optional[OrganizationSubscriptionDTO] = None
#
#     class Config:
#         orm_mode = True
#         json_encoders = {
#             datetime: lambda v: v.strftime('%Y-%m-%d') if v else None
#         }
#
# class UserPermission(BaseModel):
#     id: int
#     name: str
#     permission: dict
#
#     class Config:
#         orm_mode = True
#
# class UserDTO(BaseModel):
#     id: Optional[int] = None
#     customer_id: Optional[str] = None
#     first_name: str
#     last_name: str
#     email_id: str
#     mobile_no: str
#     address: AddressDTO
#     organization: OrganizationDTO
#     login: Optional[LoginDTO] = None
#     role: Optional[RoleDTO] = None
#     permission: Optional[UserPermission] = None
#
#     class Config:
#         orm_mode = True
#
# class PermissionUser(BaseModel):
#     id: Optional[int] = None
#     customer_id: Optional[str] = None
#     first_name: str
#     last_name: str
#     email_id: str
#     mobile_no: str
#     address: AddressDTO
#     organization: OrganizationDTO
#     login: Optional[LoginDTO] = None
#     role: Optional[RoleDTO] = None
#
#     class Config:
#         orm_mode = True
#
# class PermissionDTO(BaseModel):
#     id: int
#     name: str
#     permission: dict  # You can use a more specific type if known.
#     user:  Optional[PermissionUser] = None
#
#     class Config:
#         orm_mode = True
