# patches.py
import httpx
import os
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Store the original request method
original_request = httpx.Client.request

# Set a reasonable timeout that is longer than default but won't cause worker timeouts
OLLAMA_TIMEOUT = float(os.environ.get('OLLAMA_TIMEOUT', '60.0'))  # Default 60 seconds

@wraps(original_request)
def patched_request(self, *args, **kwargs):
    # Set default timeout if not explicitly provided
    if 'timeout' not in kwargs:
        kwargs['timeout'] = OLLAMA_TIMEOUT
        logger.debug(f"Added default timeout of {OLLAMA_TIMEOUT}s to httpx request")
    return original_request(self, *args, **kwargs)

# Apply the patch
httpx.Client.request = patched_request