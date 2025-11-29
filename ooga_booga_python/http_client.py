import asyncio
import aiohttp
import json
from typing import Dict, List, Union, Optional, NoReturn
from .custom_logger import get_logger
from .exceptions import (
    APIRequestError,
    APINotFoundError,
    APIValidationError,
    APIRateLimitError,
    APIServerError
)

logger = get_logger(__name__)


class HTTPClient:
    """Handles HTTP requests with retry logic and error handling."""

    def __init__(self, headers: Dict[str, str], max_retries: int = 5, request_delay: float = 1.0):
        self.headers = headers
        self.max_retries = max_retries
        self.request_delay = request_delay

    async def get(self, url: str, params: Optional[Dict] = None) -> Union[Dict, List]:
        """
        Sends a GET request with retry logic.

        Args:
            url: The endpoint URL.
            params: Query parameters for the request.

        Returns:
            Union[Dict, List]: JSON response data.

        Raises:
            APIRequestError: If the request fails after retries.
            APIValidationError: For validation errors (422).
            APINotFoundError: For 404 errors.
            APIRateLimitError: For rate limit errors (429).
            APIServerError: For server errors (5xx).
        """
        retry = 0
        async with aiohttp.ClientSession() as session:
            while retry < self.max_retries:
                try:
                    async with session.get(url, headers=self.headers, params=params) as response:
                        return await self._handle_response(response, url)
                except aiohttp.ClientError as e:
                    if not self._should_retry_error(e):
                        raise
                    logger.error(f"Client error occurred: {e}")
                    retry += 1
                    await asyncio.sleep(self.request_delay)
        raise APIRequestError(f"Failed to fetch data from {url} after {self.max_retries} retries.")

    async def post(self, url: str, json_data: Optional[Dict] = None) -> Union[Dict, List]:
        """
        Sends a POST request with retry logic.

        Args:
            url: The endpoint URL.
            json_data: JSON payload for the request.

        Returns:
            Union[Dict, List]: JSON response data.

        Raises:
            APIRequestError: If the request fails after retries.
            APIValidationError: For validation errors (422).
            APINotFoundError: For 404 errors.
            APIRateLimitError: For rate limit errors (429).
            APIServerError: For server errors (5xx).
        """
        retry = 0
        async with aiohttp.ClientSession() as session:
            while retry < self.max_retries:
                try:
                    async with session.post(url, headers=self.headers, json=json_data) as response:
                        return await self._handle_response(response, url)
                except aiohttp.ClientError as e:
                    if not self._should_retry_error(e):
                        raise
                    logger.error(f"Client error occurred: {e}")
                    retry += 1
                    await asyncio.sleep(self.request_delay)
        raise APIRequestError(f"Failed to post data to {url} after {self.max_retries} retries.")

    async def _handle_response(self, response: aiohttp.ClientResponse, url: str) -> Union[Dict, List]:
        """Handle HTTP response based on status code."""
        if response.status == 200:
            json_data = await response.json()
            if not isinstance(json_data, (dict, list)):
                raise APIRequestError(f"Expected JSON object from {url}, got {type(json_data).__name__}")
            return json_data
        elif response.status == 404:
            raise APINotFoundError(f"Resource not found at {url}.")
        elif response.status == 422:
            await self._handle_validation_error(response)
        elif response.status == 429:
            raise APIRateLimitError(f"Rate limit exceeded for {url}.")
        elif 500 <= response.status < 600:
            raise APIServerError(f"Server error: {response.status} at {url}.")
        else:
            # For other errors, log and potentially retry
            error_text = await response.text()
            logger.error(f"HTTP error {response.status}: {error_text}")
            raise aiohttp.ClientResponseError(
                request_info=response.request_info,
                history=response.history,
                status=response.status
            )

    @staticmethod
    async def _handle_validation_error(response: aiohttp.ClientResponse) -> NoReturn:
        """Handle 422 validation errors."""
        # Read response as text first
        try:
            error_text = await response.text()
        except Exception:
            error_text = ""

        # If no response text, provide a default message
        if not error_text.strip():
            raise APIValidationError("Validation error: Invalid request")

        try:
            # Try to parse the text as JSON
            error_data = json.loads(error_text)
            if isinstance(error_data, dict):
                # More intelligent error parsing based on the error structure
                found_value = error_data.get('found', '')
                message = error_data.get('message', '')
                summary = error_data.get('summary', '')

                # Check if it's a token address (starts with 0x and is long)
                if found_value and isinstance(found_value, str) and found_value.startswith('0x') and len(
                        found_value) > 10:
                    raise APIValidationError(f"Invalid token address: {found_value}")

                # Check if it's a slippage validation error
                elif found_value and ('Expected number' in message or 'Expected number' in summary):
                    try:
                        slippage_val = float(found_value)
                        if slippage_val > 1.0:
                            raise APIValidationError(f"Slippage too high: {slippage_val}. Must be ≤ 1.0 (100%)")
                        else:
                            raise APIValidationError(f"Invalid slippage value: {found_value}. {message}")
                    except ValueError:
                        raise APIValidationError(f"Invalid slippage format: {found_value}. {message}")

                # Generic validation error with context
                elif found_value:
                    raise APIValidationError(f"Validation error: {message or summary} - found: {found_value}")
                else:
                    raise APIValidationError(f"Validation error: {error_text}")
            else:
                raise APIValidationError(f"Validation error: {error_text}")
        except (json.JSONDecodeError, KeyError, TypeError):
            # If JSON parsing fails, use the raw text
            raise APIValidationError(f"Validation error: {error_text}")

    @staticmethod
    def _should_retry_error(error: Exception) -> bool:
        """Determine if an error should be retried."""
        # Don't retry validation errors
        if "422" in str(error):
            return False
        return True