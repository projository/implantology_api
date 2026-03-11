# app/main.py

import multiprocessing
multiprocessing.set_start_method("spawn", force=True)

import logging
import logging.config
import yaml
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from starlette.middleware.cors import CORSMiddleware

from app.services.engine_service import load_model
from app.core.config import settings
from app.utils.database import (
    connect_to_mongo,
    close_mongo_connection,
    create_indexes,
)

# Import all routers
from app.routes.auth_routes import router as auth_router
from app.routes.attachment_routes import router as attachment_router
from app.routes.constant_routes import router as constant_router
from app.routes.message_routes import router as message_router
from app.routes.testimonial_routes import router as testimonial_router
from app.routes.carousel_routes import router as carousel_router
from app.routes.doctor_routes import router as doctor_router
from app.routes.data_type_routes import router as data_type_router
from app.routes.instructor_routes import router as instructor_router
from app.routes.category_routes import router as category_router
from app.routes.course_routes import router as course_router
from app.routes.gallery_routes import router as gallery_router
from app.routes.blog_routes import router as blog_router
from app.routes.review_routes import router as review_router
from app.routes.payment_routes import router as payment_router
from app.routes.enrollment_routes import router as enrollment_router
from app.routes.faq_routes import router as faq_router
from app.routes.intent_routes import router as intent_router
from app.routes.chat_routes import router as chat_router
from app.routes.conversation_routes import router as conversation_router
from app.routes.socket_routes import router as socket_router

# ---------------------------------------------------
# Logging Configuration
# ---------------------------------------------------

with open("logging_config.yaml", "r") as f:
    config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)

logger = logging.getLogger(__name__)


# ---------------------------------------------------
# Lifespan (Startup & Shutdown)
# ---------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting application...")

    # Connect MongoDB
    await connect_to_mongo()

    # Ensure indexes
    await create_indexes()

    # Load embedding model
    load_model()

    logger.info("✅ Application startup completed.")

    yield

    # Shutdown section
    logger.info("🛑 Shutting down application...")

    await close_mongo_connection()

    logger.info("✅ Shutdown completed.")


# ---------------------------------------------------
# FastAPI App
# ---------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------
# CORS Configuration
# ---------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------
# Global Exception Handler
# ---------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


# ---------------------------------------------------
# Health Check Endpoint
# ---------------------------------------------------

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# ---------------------------------------------------
# Root Endpoint
# ---------------------------------------------------

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}"}


# ---------------------------------------------------
# Include Routers
# ---------------------------------------------------

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(attachment_router, prefix="/attachments", tags=["Attachment"])
app.include_router(constant_router, prefix="/constants", tags=["Constant"])
app.include_router(message_router, prefix="/messages", tags=["Message"])
app.include_router(testimonial_router, prefix="/testimonials", tags=["Testimonial"])
app.include_router(carousel_router, prefix="/carousels", tags=["Carousel"])
app.include_router(doctor_router, prefix="/doctors", tags=["Doctor"])
app.include_router(data_type_router, prefix="/data-types", tags=["Data Type"])
app.include_router(instructor_router, prefix="/instructors", tags=["Instructor"])
app.include_router(category_router, prefix="/categories", tags=["Category"])
app.include_router(course_router, prefix="/courses", tags=["Course"])
app.include_router(gallery_router, prefix="/galleries", tags=["Gallery"])
app.include_router(blog_router, prefix="/blogs", tags=["Blog"])
app.include_router(review_router, prefix="/reviews", tags=["Review"])
app.include_router(payment_router, prefix="/payments", tags=["Payment"])
app.include_router(enrollment_router, prefix="/enrollments", tags=["Enrollment"])
app.include_router(faq_router, prefix="/faqs", tags=["FAQ"])
app.include_router(intent_router, prefix="/intents", tags=["Intent"])
app.include_router(chat_router, prefix="/chats", tags=["Chat"])
app.include_router(conversation_router, prefix="/conversations", tags=["Conversation"])
app.include_router(socket_router, tags=["Socket"])