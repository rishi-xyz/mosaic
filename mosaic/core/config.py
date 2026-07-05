import os
import cognee


def configure_graph(config: dict | None = None):
    """Configure graph database with optional config dict.
    
    Args:
        config: Optional config dict. If not provided, uses os.environ.
    """
    env = config if config else os.environ
    provider = env.get("GRAPH_DATABASE_PROVIDER", "")

    if provider == "neo4j" and env.get("GRAPH_DATABASE_URL"):
        cognee.config.set("graph_database_provider", "neo4j")
        cognee.config.set_graph_db_config({
            "graph_database_url": env["GRAPH_DATABASE_URL"],
            "graph_database_username": env.get("GRAPH_DATABASE_USERNAME", ""),
            "graph_database_password": env.get("GRAPH_DATABASE_PASSWORD", ""),
            "graph_database_name": env.get("GRAPH_DATABASE_NAME", ""),
            "graph_database_allow_anonymous": (
                env.get("GRAPH_DATABASE_ALLOW_ANONYMOUS", "").lower() == "true"
            ),
        })


def configure_cognee(config: dict | None = None):
    """Configure Cognee with optional config dict.
    
    Args:
        config: Optional config dict. If not provided, uses os.environ.
                Expected keys: OPENROUTER_API_KEY, LLM_ENDPOINT, LLM_MODEL,
                EMBEDDING_ENDPOINT, EMBEDDING_MODEL, COGNEE_LLM_MODEL,
                COGNEE_EMBEDDING_MODEL, and graph database keys.
    """
    env = config if config else os.environ
    
    cognee.config.set("data_root_directory", os.path.join(os.getcwd(), ".data_storage"))
    api_key = env.get("OPENROUTER_API_KEY", "")

    if api_key:
        llm_endpoint = "https://openrouter.ai/api/v1"
        embedding_endpoint = "https://openrouter.ai/api/v1"
        llm_model = env.get(
            "COGNEE_LLM_MODEL",
            "openrouter/google/gemma-4-26b-a4b-it:free",
        )
        embedding_model = env.get(
            "COGNEE_EMBEDDING_MODEL",
            "openrouter/nvidia/llama-nemotron-embed-vl-1b-v2:free",
        )
        embedding_provider = "custom"
    else:
        # Only set os.environ defaults if we're using global env (config is None)
        if config is None:
            os.environ.setdefault("STRUCTURED_OUTPUT_FRAMEWORK", "baml")
            os.environ.setdefault("CACHING", "false")
        llm_endpoint = env.get("LLM_ENDPOINT", "http://localhost:11434/v1")
        llm_model = env.get("LLM_MODEL", "llama3.2:3b")
        raw_model = env.get("EMBEDDING_MODEL", "nomic-embed-text")
        embedding_model = raw_model
        embedding_endpoint = env.get("EMBEDDING_ENDPOINT", "http://localhost:11434")
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

    configure_graph(config)
