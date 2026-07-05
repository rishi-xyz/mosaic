import os
import cognee


def configure_cognee():
    api_key = os.environ.get("OPENROUTER_API_KEY", "")

    if api_key:
        llm_endpoint = "https://openrouter.ai/api/v1"
        embedding_endpoint = "https://openrouter.ai/api/v1"
        llm_model = os.environ.get(
            "COGNEE_LLM_MODEL",
            "openrouter/google/gemma-4-26b-a4b-it:free",
        )
        embedding_model = os.environ.get(
            "COGNEE_EMBEDDING_MODEL",
            "openrouter/nvidia/llama-nemotron-embed-vl-1b-v2:free",
        )
    else:
        llm_endpoint = os.environ.get("LLM_ENDPOINT", "http://localhost:11434/v1")
        embedding_endpoint = os.environ.get("EMBEDDING_ENDPOINT", "http://localhost:11434/v1")
        llm_model = os.environ.get("LLM_MODEL", "llama3.2:3b")
        embedding_model = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text")
        api_key = "ollama"

    cognee.config.set("llm_provider", "custom")
    cognee.config.set("llm_endpoint", llm_endpoint)
    cognee.config.set("llm_api_key", api_key)
    cognee.config.set("llm_model", llm_model)
    cognee.config.set("embedding_provider", "custom")
    cognee.config.set("embedding_endpoint", embedding_endpoint)
    cognee.config.set("embedding_api_key", api_key)
    cognee.config.set("embedding_model", embedding_model)
