import logging
import logging.config
import yaml
from fastapi import FastAPI
from contextlib import asynccontextmanager
from starlette.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.utils.database import create_indexes
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

# Load logging configuration
with open("logging_config.yaml", "r") as f:
    config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(attachment_router, prefix="/attachments", tags=["Attachment"])
app.include_router(constant_router, prefix="/constant", tags=["Constant"])
app.include_router(message_router, prefix="/messages", tags=["Message"])
app.include_router(testimonial_router, prefix="/testimonials", tags=["Testimonial"])
app.include_router(carousel_router, prefix="/carousels", tags=["Carousel"])
app.include_router(doctor_router, prefix="/doctors", tags=["Doctor"])
app.include_router(data_type_router, prefix="/data_types", tags=["Data Type"])
app.include_router(instructor_router, prefix="/instructors", tags=["Instructor"])
app.include_router(category_router, prefix="/categories", tags=["Category"])
app.include_router(course_router, prefix="/courses", tags=["Course"])
app.include_router(gallery_router, prefix="/galleries", tags=["Gallery"])
app.include_router(blog_router, prefix="/blogs", tags=["Blog"])

@app.get("/")
def read_root():
    return {"message": "Welcome to my FastAPI app"}
