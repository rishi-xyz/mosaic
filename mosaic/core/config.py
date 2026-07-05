import os
import cognee


def configure_cognee():
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    llm_model = os.environ.get(
        "COGNEE_LLM_MODEL",
        "openrouter/google/gemma-4-26b-a4b-it:free",
    )
    embedding_model = os.environ.get(
        "COGNEE_EMBEDDING_MODEL",
        "openrouter/nvidia/llama-nemotron-embed-vl-1b-v2:free",
    )

    cognee.config.set("llm_provider", "custom")
    cognee.config.set("llm_endpoint", "https://openrouter.ai/api/v1")
    cognee.config.set("llm_api_key", api_key)
    cognee.config.set("llm_model", llm_model)
    cognee.config.set("embedding_provider", "custom")
    cognee.config.set("embedding_endpoint", "https://openrouter.ai/api/v1")
    cognee.config.set("embedding_api_key", api_key)
    cognee.config.set("embedding_model", embedding_model)
