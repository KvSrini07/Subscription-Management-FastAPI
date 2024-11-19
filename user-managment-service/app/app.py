import logging
from fastapi import FastAPI
from app.configuration.db import init_db
from app.configuration.config import load_env
from app.routers.subscription_router import subscription_router
# from app.routers.user_router import user_router, permission_router, role_router

# Load environment variables
load_env()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(subscription_router, prefix="/v1/api/subscriptions", tags=["Subscription"])

@app.on_event("startup")
async def startup_event():
    try:
        await init_db()
        logger.info("Application startup successful")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting application...")
    uvicorn.run(app, host="0.0.0.0", port=5002)
