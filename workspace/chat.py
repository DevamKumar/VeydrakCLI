def get_client(api_key):
    """Create and return an API client."""
    return {"api_key": api_key, "base_url": "https://api.openai.com/v1"}


def stream_response(client, messages, system_prompt=None):
    """Stream a chat response. Yields message chunks. Prepend a system message if provided."""
    if system_prompt:
        yield f"System: {system_prompt}"
    for msg in messages:
        yield f"Response to: {msg.get('content', '')}"
