import pytest
import asyncio
import aiohttp
from unittest.mock import AsyncMock, patch, MagicMock
from ooga_booga_python.http_client import HTTPClient
from ooga_booga_python.exceptions import (
    APIRequestError,
    APINotFoundError,
    APIValidationError,
    APIRateLimitError,
    APIServerError
)


@pytest.fixture
def http_client():
    """Create an HTTPClient instance for testing."""
    return HTTPClient(
        headers={"Authorization": "Bearer test_key"},
        max_retries=3,
        request_delay=0.1  # Short delay for faster tests
    )


class TestHTTPClientErrors:
    """Test error handling in HTTPClient."""

    @pytest.mark.asyncio
    async def test_404_not_found(self, http_client):
        """Test 404 error handling."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock response with 404 status
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_get.return_value.__aenter__.return_value = mock_response

            with pytest.raises(APINotFoundError) as exc_info:
                await http_client.get("https://api.example.com/not-found")

            assert "Resource not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_422_validation_error_with_token_address(self, http_client):
        """Test 422 validation error with invalid token address."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 422
            mock_response.text.return_value = '{"type":"validation","on":"property","found":"0xInvalidAddress"}'
            mock_get.return_value.__aenter__.return_value = mock_response

            with pytest.raises(APIValidationError) as exc_info:
                await http_client.get("https://api.example.com/approve?token=0xInvalidAddress")

            assert "Invalid token address: 0xInvalidAddress" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_422_validation_error_without_found_field(self, http_client):
        """Test 422 validation error without 'found' field."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 422
            mock_response.text.return_value = '{"error":"Invalid input data"}'
            mock_get.return_value.__aenter__.return_value = mock_response

            with pytest.raises(APIValidationError) as exc_info:
                await http_client.get("https://api.example.com/validate")

            assert "Validation error:" in str(exc_info.value)
            assert "Invalid input data" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_422_validation_error_invalid_json(self, http_client):
        """Test 422 validation error with invalid JSON response."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 422
            mock_response.text.return_value = "Plain text error message"
            mock_get.return_value.__aenter__.return_value = mock_response

            with pytest.raises(APIValidationError) as exc_info:
                await http_client.get("https://api.example.com/validate")

            assert "Validation error: Plain text error message" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_429_rate_limit_error(self, http_client):
        """Test 429 rate limit error handling."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 429
            mock_get.return_value.__aenter__.return_value = mock_response

            with pytest.raises(APIRateLimitError) as exc_info:
                await http_client.get("https://api.example.com/data")

            assert "Rate limit exceeded" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_500_server_error(self, http_client):
        """Test 500 server error handling."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_get.return_value.__aenter__.return_value = mock_response

            with pytest.raises(APIServerError) as exc_info:
                await http_client.get("https://api.example.com/data")

            assert "Server error: 500" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_503_server_error(self, http_client):
        """Test 503 server error handling."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 503
            mock_get.return_value.__aenter__.return_value = mock_response

            with pytest.raises(APIServerError) as exc_info:
                await http_client.get("https://api.example.com/data")

            assert "Server error: 503" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_other_http_error(self, http_client):
        """Test other HTTP status codes that should be retried and eventually fail."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 418  # I'm a teapot
            mock_response.text.return_value = "I'm a teapot"
            mock_response.request_info = MagicMock()
            mock_response.history = []
            mock_get.return_value.__aenter__.return_value = mock_response

            # Other HTTP errors get retried and eventually raise APIRequestError
            with pytest.raises(APIRequestError) as exc_info:
                await http_client.get("https://api.example.com/teapot")

            assert "Failed to fetch data" in str(exc_info.value)
            assert "after 3 retries" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_json_response_type(self, http_client):
        """Test response that's not a dict or list."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = "just a string"  # Invalid JSON type
            mock_get.return_value.__aenter__.return_value = mock_response

            with pytest.raises(APIRequestError) as exc_info:
                await http_client.get("https://api.example.com/data")

            assert "Expected JSON object" in str(exc_info.value)
            assert "got str" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_network_error_retries(self, http_client):
        """Test network errors that should be retried."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Simulate network error that should be retried
            mock_get.side_effect = aiohttp.ClientConnectorError(
                connection_key=MagicMock(),
                os_error=OSError("Connection failed")
            )

            with pytest.raises(APIRequestError) as exc_info:
                await http_client.get("https://api.example.com/data")

            assert "Failed to fetch data" in str(exc_info.value)
            assert "after 3 retries" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_422_network_error_no_retry(self, http_client):
        """Test that 422 network errors are not retried."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Simulate a 422 error in the network layer
            mock_get.side_effect = aiohttp.ClientError("422, message='Validation error'")

            with pytest.raises(aiohttp.ClientError):
                await http_client.get("https://api.example.com/data")

            # Should not retry, so mock should only be called once
            assert mock_get.call_count == 1

    @pytest.mark.asyncio
    async def test_successful_dict_response(self, http_client):
        """Test successful response with dictionary."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"success": True, "data": "test"}
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await http_client.get("https://api.example.com/data")

            assert result == {"success": True, "data": "test"}

    @pytest.mark.asyncio
    async def test_successful_list_response(self, http_client):
        """Test successful response with list."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = [{"id": 1}, {"id": 2}]
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await http_client.get("https://api.example.com/data")

            assert result == [{"id": 1}, {"id": 2}]

    @pytest.mark.asyncio
    async def test_retry_after_transient_error(self, http_client):
        """Test successful retry after transient error."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Create success response
            mock_response_success = AsyncMock()
            mock_response_success.status = 200
            mock_response_success.json.return_value = {"success": True}

            # Create a proper context manager mock
            mock_cm_success = AsyncMock()
            mock_cm_success.__aenter__.return_value = mock_response_success
            mock_cm_success.__aexit__.return_value = None

            # First call fails, second call succeeds
            call_count = 0

            def side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise aiohttp.ClientConnectorError(
                        connection_key=MagicMock(),
                        os_error=OSError("Temporary network error")
                    )
                else:
                    return mock_cm_success

            mock_get.side_effect = side_effect

            result = await http_client.get("https://api.example.com/data")

            assert result == {"success": True}
            assert call_count == 2  # One failure, one success

    @pytest.mark.asyncio
    async def test_exhausted_retries(self, http_client):
        """Test behavior when all retries are exhausted."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # All calls fail with retryable errors
            mock_get.side_effect = aiohttp.ClientConnectorError(
                connection_key=MagicMock(),
                os_error=OSError("Persistent network error")
            )

            with pytest.raises(APIRequestError) as exc_info:
                await http_client.get("https://api.example.com/data")

            assert "Failed to fetch data" in str(exc_info.value)
            assert "after 3 retries" in str(exc_info.value)
            assert mock_get.call_count == 3  # max_retries
