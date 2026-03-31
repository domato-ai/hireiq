"""Azure OpenAI client wrapper with retry and token tracking."""
from __future__ import annotations
import json
import logging
from openai import AsyncAzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import get_settings

logger = logging.getLogger(__name__)

_client: AsyncAzureOpenAI | None = None

def get_client() -> AsyncAzureOpenAI:
    global _client
    if _client is None:
        s = get_settings()
        _client = AsyncAzureOpenAI(
            azure_endpoint=s.azure_openai_endpoint,
            api_key=s.azure_openai_api_key,
            api_version=s.azure_openai_api_version,
        )
    return _client

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def complete(prompt: str, system: str = "", model: str | None = None) -> str:
    """Get a text completion from Azure OpenAI."""
    s = get_settings()
    deployment = model or s.azure_openai_deployment_mini
    client = get_client()

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = await client.chat.completions.create(
        model=deployment,
        messages=messages,
        temperature=0.1,
        max_tokens=2000,
    )

    result = response.choices[0].message.content or ""
    logger.info("LLM call: %s, tokens: %d in / %d out", deployment,
                response.usage.prompt_tokens if response.usage else 0,
                response.usage.completion_tokens if response.usage else 0)
    return result

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def extract_json(prompt: str, system: str = "", model: str | None = None) -> dict:
    """Get a JSON response from Azure OpenAI."""
    s = get_settings()
    deployment = model or s.azure_openai_deployment_mini
    client = get_client()

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = await client.chat.completions.create(
        model=deployment,
        messages=messages,
        temperature=0.0,
        max_tokens=3000,
        response_format={"type": "json_object"},
    )

    text = response.choices[0].message.content or "{}"
    logger.info("LLM JSON call: %s, tokens: %d in / %d out", deployment,
                response.usage.prompt_tokens if response.usage else 0,
                response.usage.completion_tokens if response.usage else 0)
    return json.loads(text)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def embed(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts."""
    s = get_settings()
    client = get_client()

    response = await client.embeddings.create(
        input=texts,
        model=s.azure_openai_deployment_embedding,
    )

    logger.info("Embedding call: %d texts, %d tokens", len(texts),
                response.usage.total_tokens if response.usage else 0)
    return [item.embedding for item in response.data]
