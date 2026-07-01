import asyncio
import os
import cognee
from cognee.modules.search.types import SearchType

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "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")

async def test_cognee():
    cognee.config.set("llm_provider", "custom") 
    cognee.config.set("llm_endpoint", "https://openrouter.ai/api/v1")
    cognee.config.set("llm_api_key", OPENROUTER_API_KEY)
    cognee.config.set("llm_model", "openrouter/google/gemma-4-26b-a4b-it:free")
    cognee.config.set("embedding_provider","custom")
    cognee.config.set("embedding_endpoint", "https://openrouter.ai/api/v1")
    cognee.config.set("embedding_api_key", OPENROUTER_API_KEY)
    cognee.config.set("embedding_model", "openrouter/nvidia/llama-nemotron-embed-vl-1b-v2:free")

    print("---  Testing Cognee with OpenRouter Free Models ---")
    

    sample_text = (
        "Cognee is an open-source memory engine for AI agents. "
        "It connects structured graphs and vectors to help agents remember facts."
    )

    try:
        print("\n[1/3] Adding text content to Cognee...")
        await cognee.add(
            data=sample_text,
            dataset_name="openrouter_test_dataset"
        )
        
        print("[2/3] Processing text via OpenRouter ('Cognifying')...")
        await cognee.cognify()
        
        print("[3/3] Searching the memory layer...")
        search_results = await cognee.search(
            query_text="What does Cognee connect?",
            query_type=SearchType.GRAPH_COMPLETION
        )
        
        print("\n--- 🎉 Success! Search Results ---")
        print(search_results)

    except Exception as e:
        print(f"\n❌ Error encountered: {e}")
        print("Tip: Ensure your OpenRouter key is valid and the selected free model is available.")

if __name__ == "__main__":
    asyncio.run(test_cognee())
