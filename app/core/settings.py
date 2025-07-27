from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    clova_api_host: str
    clova_api_key: str
    clova_request_id: str
    dart_retriever_url: str
    news_retriever_url: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
