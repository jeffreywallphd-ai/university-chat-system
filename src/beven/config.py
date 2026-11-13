"""
Local retrieval-augmented answering.

Memory is a vector store (Chroma, or Postgres/pgvector). A graph database is
not used: questions look up similar page text, not relationships between
records. Chroma and pgvector store vectors; they do not create them.
Embeddings are computed locally in app/embed.py.

LangChain builds the prompt and runs the model. The model itself is hosted
here: Hugging Face Transformers by default, or Ollama on localhost when
LLM_BACKEND=ollama. Retrieved campus text is not sent to an external API.
"""
from dataclasses import dataclass, field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    # LLM configuration
    llm_backend: str = "transformers"  # transformers | ollama
    llm_model: str = "Qwen/Qwen2.5-0.5B-Instruct"
    ollama_base_url: str = "http://127.0.0.1:11434"
    max_new_tokens: int = 320
    # Embedding configuration
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    chroma_dir: str = "./chroma_data"
    # Ingestion configuration
    user_agent: str = "NovusPal/1.0"
    admin_api_key: str = "change_me"
    request_delay_s: float = 2.0
    max_pages_per_source: int = 50
    # Backend selection
    vector_backend: str = "chroma"  # chroma | pgvector
    database_url: str = "postgresql://novuspal:novuspal@localhost:5432/novuspal"
    cors_origins: str = "*"


class Sources(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    sources: dict = {
        "mtu-news": "https://news.mtu.edu/",
        "mtu-events": "https://events.mtu.edu/",
        "mtu-library": "https://library.mtu.edu/",
        "mtu-career": "https://career.mtu.edu/",
        "mtu-housing": "https://housing.mtu.edu/",
        "mtu-registration": "https://registration.mtu.edu/",
        "mtu-tutoring": "https://tutoring.mtu.edu/",
        "mtu-dean": "https://deanofstudents.mtu.edu/",
        "mtu-safety": "https://www.mtu.edu/publicsafety/",
        "mtu-well-being": "https://www.mtu.edu/well-being/",
        "mtu-it": "https://www.mtu.edu/it/help/",
        "mtu-finaid": "https://www.mtu.edu/finaid/",
        "mtu-admissions": "https://www.mtu.edu/admissions/financial/tuition/",
        "mtu-michigantechrecreation": "https://michigantechrecreation.com/",
    }


# Instantiate settings
settings = Settings()
source_settings = Sources()