class APIClientError(Exception):
    """
    Raised for errors related to API client configuration, such as missing API keys.
    """
    def __init__(self, message: str = "An error occurred with the API client configuration."):
        super().__init__(message)


class APIRequestError(Exception):
    """
    Raised for errors during API requests, such as connection issues or server errors.
    """
    def __init__(self, message: str = "An error occurred during the API request."):
        super().__init__(message)


class ValidationError(Exception):
    """
    Raised for data validation errors, such as incorrect parameters or invalid responses.
    """
    def __init__(self, message: str = "Data validation failed."):
        super().__init__(message)


class APIRateLimitError(Exception):
    """
    Raised when the API rate limit is exceeded.
    """
    def __init__(self, message: str = "API rate limit exceeded."):
        super().__init__(message)


class APIServerError(Exception):
    """
    Raised for server-side errors (5xx HTTP responses).
    """
    def __init__(self, message: str = "Server encountered an error."):
        super().__init__(message)


class APINotFoundError(Exception):
    """
    Raised when a requested resource is not found (404 HTTP response).
    """
    def __init__(self, message: str = "The requested resource was not found."):
        super().__init__(message)

class APIValidationError(Exception):
    """
    Raised for API validation errors, such as invalid request parameters.
    """
    def __init__(self, message: str = "API request validation failed."):
        super().__init__(message)
