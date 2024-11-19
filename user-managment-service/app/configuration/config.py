import os
from dotenv import load_dotenv

def load_env():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))    
    # Path to the .env file
    dotenv_path = os.path.join(project_root, '.env')
    load_dotenv(dotenv_path)

class Config:
    load_env()
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")

    API_URL = os.getenv("API_URL")
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    LOG_TO_FILE = os.getenv("LOG_TO_FILE", "True").lower() == "true"
    LOG_TO_CONSOLE = os.getenv("LOG_TO_CONSOLE", "True").lower() == "true"

    # SuperAdmin Configuration
    SUPERADMIN_ROLE: str = os.getenv("SUPERADMIN_ROLE")
    SUPERADMIN_DESCRIPTION: str = os.getenv("SUPERADMIN_DESCRIPTION")
    SUPERADMIN_EMAIL: str = os.getenv("SUPERADMIN_EMAIL")
    SUPERADMIN_PASSWORD: str = os.getenv("SUPERADMIN_PASSWORD")
    SUPERADMIN_FIRSTNAME: str = os.getenv("SUPERADMIN_FIRSTNAME")
    SUPERADMIN_LASTNAME: str = os.getenv("SUPERADMIN_LASTNAME")
    SUPERADMIN_MOBILE: str = os.getenv("SUPERADMIN_MOBILE")
    SUPERADMIN_ADDRESS_LINE1: str = os.getenv("SUPERADMIN_ADDRESS_LINE1")
    SUPERADMIN_ADDRESS_LINE2: str = os.getenv("SUPERADMIN_ADDRESS_LINE2")
    SUPERADMIN_ADDRESS_CITY: str = os.getenv("SUPERADMIN_ADDRESS_CITY")
    SUPERADMIN_ADDRESS_STATE: str = os.getenv("SUPERADMIN_ADDRESS_STATE")
    SUPERADMIN_ADDRESS_COUNTRY: str = os.getenv("SUPERADMIN_ADDRESS_COUNTRY")
    SUPERADMIN_ADDRESS_PINCODE: str = os.getenv("SUPERADMIN_ADDRESS_PINCODE")
    SUPERADMIN_ORGANIZATION_NAME: str = os.getenv("SUPERADMIN_ORGANIZATION_NAME")
    SUPERADMIN_ORGANIZATION_DISPLAY_NAME: str = os.getenv("SUPERADMIN_ORGANIZATION_DISPLAY_NAME")
    SUPERADMIN_ORGANIZATION_GSTIN: str = os.getenv("SUPERADMIN_ORGANIZATION_GSTIN")
    SUPERADMIN_ORGANIZATION_PAN: str = os.getenv("SUPERADMIN_ORGANIZATION_PAN")
    SUPERADMIN_ORGANIZATION_TAN: str = os.getenv("SUPERADMIN_ORGANIZATION_TAN")
    SUPERADMIN_ORGANIZATION_TYPE: str = os.getenv("SUPERADMIN_ORGANIZATION_TYPE")
    SUPERADMIN_ORGANIZATION_INCORPORATION_DATE: str = os.getenv("SUPERADMIN_ORGANIZATION_INCORPORATION_DATE")
    SUPERADMIN_ORGANIZATION_CIN: str = os.getenv("SUPERADMIN_ORGANIZATION_CIN")

    # Default values
    ROLE_USER: str = os.getenv("ROLE_USER", "USER")
    ROLE_ADMIN: str = os.getenv("ROLE_ADMIN", "ADMIN")
    DEFAULT_ACTIVE_STATUS: bool = os.getenv("DEFAULT_ACTIVE_STATUS", "false").lower() == "true"

    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    JWT_TOKEN_VALIDITY: int = int(os.getenv("JWT_TOKEN_VALIDITY", 86400000))

    # Email Configuration
    EMAIL_HOST: str = os.getenv("EMAIL_HOST")
    EMAIL_PORT: int = int(os.getenv("EMAIL_PORT", 587))
    EMAIL_USERNAME: str = os.getenv("EMAIL_USERNAME")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD")
    EMAIL_USE_TLS: bool = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
    EMAIL_USE_SSL: bool = os.getenv("EMAIL_USE_SSL", "false").lower() == "true"
    EMAIL_FROM: str = os.getenv("EMAIL_FROM")

    # Mail subjects
    MAIL_SUBJECT_WELCOME: str = os.getenv("MAIL_SUBJECT_WELCOME")
    MAIL_SUBJECT_SUBSCRIPTION_EXPIRY: str = os.getenv("MAIL_SUBJECT_SUBSCRIPTION_EXPIRY")
    MAIL_SUBJECT_SUBSCRIPTION_EXPIRED: str = os.getenv("MAIL_SUBJECT_SUBSCRIPTION_EXPIRED")
    MAIL_SUBJECT_SUBSCRIPTION_RENEWAL_REMINDER: str = os.getenv("MAIL_SUBJECT_SUBSCRIPTION_RENEWAL_REMINDER")

    # TLS version
    EMAIL_TLS_VERSION: str = os.getenv("EMAIL_TLS_VERSION", "TLSv1.2")

    # Debugging prints to ensure variables are loaded correctly
    print(f"Loaded DB_USER: {DB_USER}")
    print(f"Loaded DB_PASSWORD: {DB_PASSWORD}")
    print(f"Loaded DB_NAME: {DB_NAME}")
    print(f"Loaded DB_HOST: {DB_HOST}")
    print(f"Loaded DB_PORT: {DB_PORT}")
