import os
from dataclasses import dataclass
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # API Keys
    openai_api_key: str
    pinecone_api_key: str
    cohere_api_key: str
    posthog_api_key: str

    # Pinecone
    pinecone_index_name: str
    pinecone_namespace: str

    # OpenAI
    embedding_model: str
    generation_model: str
    router_model: str

    # Cohere
    rerank_model: str

    # Retrieval defaults
    retrieval_k: int
    final_k: int
    hybrid_alpha: float

    # Artifacts
    bm25_encoder_path: str

    # CORS
    frontend_url: str

@lru_cache
def get_settings() -> Settings:
    return Settings(
        # API Keys
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        pinecone_api_key=os.getenv("PINECONE_API_KEY", ""),
        cohere_api_key=os.getenv("COHERE_API_KEY", ""),
        posthog_api_key=os.getenv("POSTHOG_API_KEY", ""),

        # Pinecone
        pinecone_index_name=os.getenv("PINECONE_INDEX_NAME", "islamic-rag-hybrid"),
        pinecone_namespace=os.getenv("PINECONE_NAMESPACE", "islamic-rag-v1"),

        # OpenAI
        embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large"),
        generation_model=os.getenv("OPENAI_GENERATION_MODEL", "gpt-5.6-terra"),
        router_model=os.getenv("OPENAI_ROUTER_MODEL", "gpt-5.6-luna"),

        # Cohere
        rerank_model=os.getenv("COHERE_RERANK_MODEL", "rerank-v4.0-pro"),

        # Retrieval defaults
        retrieval_k=int(os.getenv("RETRIEVAL_K", "40")),
        final_k=int(os.getenv("FINAL_K", "5")),
        hybrid_alpha=float(os.getenv("HYBRID_ALPHA", "0.8")),

        # Artifacts
        bm25_encoder_path=os.getenv(
            "BM25_ENCODER_PATH",
            "artifacts/bm25_encoder.pkl"
        ),

        # CORS
        frontend_url=os.getenv("FRONTEND_URL", "http://localhost:5173"),
    )


settings = get_settings()