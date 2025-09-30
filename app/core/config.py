from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    ENV: str
    APP_NAME: str
    SECRET_KEY: str
    DATABASE_URL: str
    DATABASE_NAME: str
    ALLOWED_ORIGINS: List[str]
    ALLOWED_IMAGE_EXTENSIONS: list[str] = Field(
        default=["jpg", "jpeg", "png", "gif"], env="ALLOWED_IMAGE_EXTENSIONS"
    )
    ALLOWED_VIDEO_EXTENSIONS: list[str] = Field(
        default=["mp4", "avi", "mov"], env="ALLOWED_VIDEO_EXTENSIONS"
    )
    ALLOWED_DOC_EXTENSIONS: list[str] = Field(
        default=["doc", "docx", "pdf", "xls", "xlsx"], env="ALLOWED_DOC_EXTENSIONS"
    )
    MAX_IMAGE_SIZE_MB: int = Field(default=8, env="MAX_IMAGE_SIZE_MB")
    MAX_VIDEO_SIZE_MB: int = Field(default=20, env="MAX_VIDEO_SIZE_MB")
    MAX_DOC_SIZE_MB: int = Field(default=20, env="MAX_DOC_SIZE_MB")

    # AWS Settings
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    S3_BUCKET_NAME: str

    # JWT Settings
    JWT_SECRET: str
    JWT_EXPIRY_IN_DAYS: int
    JWT_ALGORITHM: str

    # RAZORPAY Settings
    RAZORPAY_KEY_ID: str
    RAZORPAY_KEY_SECRET: str

    class Config:
        env_file = ".env"


settings = Settings()
