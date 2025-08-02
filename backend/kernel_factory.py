# loan_agent/backend/kernel_factory.py

import semantic_kernel as sk
from openai import AsyncOpenAI  # Import the base client
from semantic_kernel.connectors.ai.open_ai import (
    OpenAIChatCompletion,
    OpenAITextEmbedding,
)
import config

def create_kernel() -> sk.Kernel:
    """
    Initializes and returns a Semantic Kernel instance configured to use
    a custom OpenAI-compatible proxy (like ChatAnywhere).
    """
    kernel = sk.Kernel()

    # --- Create a pre-configured OpenAI client ---
    # This client will be shared by all services that connect to the proxy.
    custom_client = AsyncOpenAI(
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_BASE_URL,
    )

    # --- Add services to the kernel using the custom client ---

    # Add the chat service (for text generation like gpt-3.5-turbo)
    kernel.add_service(
        OpenAIChatCompletion(
            service_id="chat_svc",
            ai_model_id=config.CHAT_MODEL,
            async_client=custom_client,  # <-- Pass the custom client here
        ),
    )

    # Add the vision-enabled chat service (for gpt-4o image analysis)
    kernel.add_service(
        OpenAIChatCompletion(
            service_id="vision_svc",
            ai_model_id=config.VISION_MODEL,
            async_client=custom_client,  # <-- Pass the custom client here
        ),
    )

    # Add the text embedding service (for RAG)
    kernel.add_service(
        OpenAITextEmbedding(
            service_id="embedding_svc",
            ai_model_id=config.EMBEDDING_MODEL,
            async_client=custom_client,  # <-- Pass the custom client here
        ),
    )
    
    return kernel