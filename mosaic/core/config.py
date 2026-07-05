import os
import cognee


def configure_graph():
    provider = os.environ.get("GRAPH_DATABASE_PROVIDER", "")

    if provider == "neo4j" and os.environ.get("GRAPH_DATABASE_URL"):
        from cognee.infrastructure.databases.graph import get_graph_config

        graph_config = get_graph_config()
        graph_config.graph_database_provider = "neo4j"
        graph_config.graph_database_url = os.environ["GRAPH_DATABASE_URL"]
        graph_config.graph_database_username = os.environ.get("GRAPH_DATABASE_USERNAME", "")
        graph_config.graph_database_password = os.environ.get("GRAPH_DATABASE_PASSWORD", "")
        graph_config.graph_database_name = os.environ.get("GRAPH_DATABASE_NAME", "")
        graph_config.graph_database_allow_anonymous = (
            os.environ.get("GRAPH_DATABASE_ALLOW_ANONYMOUS", "").lower() == "true"
        )


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
        embedding_provider = "custom"
    else:
        os.environ.setdefault("STRUCTURED_OUTPUT_FRAMEWORK", "baml")
        os.environ.setdefault("CACHING", "false")
        llm_endpoint = os.environ.get("LLM_ENDPOINT", "http://localhost:11434/v1")
        llm_model = os.environ.get("LLM_MODEL", "llama3.2:3b")
        raw_model = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text")
        embedding_model = raw_model
        embedding_endpoint = os.environ.get("EMBEDDING_ENDPOINT", "http://localhost:11434")
        embedding_provider = "ollama"
        api_key = "ollama"

    cognee.config.set("llm_provider", "custom")
    cognee.config.set("llm_endpoint", llm_endpoint)
    cognee.config.set("llm_api_key", api_key)
    cognee.config.set("llm_model", llm_model)
    cognee.config.set("embedding_provider", embedding_provider)
    cognee.config.set("embedding_endpoint", embedding_endpoint)
    cognee.config.set("embedding_api_key", api_key)
    cognee.config.set("embedding_model", embedding_model)

    configure_graph()
