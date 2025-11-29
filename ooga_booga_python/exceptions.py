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


# ============================================================================
# Contract Error Exceptions
# ============================================================================

class ContractError(Exception):
    """
    Base class for all contract-related errors.
    """
    def __init__(self, message: str, selector: str = None, **kwargs):
        self.selector = selector
        self.details = kwargs
        super().__init__(message)


class InsufficientBalanceError(ContractError):
    """
    Raised when the user has insufficient balance of the input token.
    Selector: 0xf4d678b8
    """
    def __init__(self, **kwargs):
        super().__init__(
            "Insufficient balance of input token",
            selector="0xf4d678b8",
            **kwargs
        )


class SlippageExceededError(ContractError):
    """
    Raised when amountOut resulted lower than outputMin during swap execution.
    Selector: 0x71c4efed
    Signature: SlippageExceeded(uint256,uint256)
    """
    def __init__(self, amount_out: int = None, output_min: int = None, **kwargs):
        details = {}
        if amount_out is not None:
            details['amount_out'] = amount_out
        if output_min is not None:
            details['output_min'] = output_min
        
        message = "Slippage exceeded: amountOut resulted lower than outputMin during swap execution"
        if amount_out and output_min:
            message += f" (amountOut: {amount_out}, outputMin: {output_min})"
        
        super().__init__(
            message,
            selector="0x71c4efed",
            **{**details, **kwargs}
        )


class SameTokenInAndOutError(ContractError):
    """
    Raised when attempting to swap the same token as input and output.
    Selector: 0xfa463c69
    Signature: SameTokenInAndOut(address)
    """
    def __init__(self, token: str = None, **kwargs):
        details = {}
        if token:
            details['token'] = token
        
        message = "Cannot provide same inputToken and outputToken"
        if token:
            message += f" (token: {token})"
        
        super().__init__(
            message,
            selector="0xfa463c69",
            **{**details, **kwargs}
        )


class MinimumOutputGreaterThanQuoteError(ContractError):
    """
    Raised when outputMin is set greater than outputQuote.
    Selector: 0x6da58071
    Signature: MinimumOutputGreaterThanQuote(uint256,uint256)
    """
    def __init__(self, output_min: int = None, output_quote: int = None, **kwargs):
        details = {}
        if output_min is not None:
            details['output_min'] = output_min
        if output_quote is not None:
            details['output_quote'] = output_quote
        
        message = "outputMin is set greater than outputQuote"
        if output_min and output_quote:
            message += f" (outputMin: {output_min}, outputQuote: {output_quote})"
        
        super().__init__(
            message,
            selector="0x6da58071",
            **{**details, **kwargs}
        )


class MinimumOutputIsZeroError(ContractError):
    """
    Raised when outputMin is set to 0.
    Selector: 0xf067d762
    Signature: MinimumOutputIsZero()
    """
    def __init__(self, **kwargs):
        super().__init__(
            "outputMin is set to 0",
            selector="0xf067d762",
            **kwargs
        )


class NativeDepositValueMismatchError(ContractError):
    """
    Raised when value provided to function call does not match amountIn when inputToken is native.
    Selector: 0xdb4d141c
    Signature: NativeDepositValueMismatch(uint256,uint256)
    """
    def __init__(self, value_provided: int = None, amount_in: int = None, **kwargs):
        details = {}
        if value_provided is not None:
            details['value_provided'] = value_provided
        if amount_in is not None:
            details['amount_in'] = amount_in
        
        message = "Value provided to function call does not match amountIn when inputToken is the native token"
        if value_provided and amount_in:
            message += f" (valueProvided: {value_provided}, amountIn: {amount_in})"
        
        super().__init__(
            message,
            selector="0xdb4d141c",
            **{**details, **kwargs}
        )


class AddressEmptyCodeError(ContractError):
    """
    Raised when calling a contract that has no bytecode.
    Selector: 0x9996b315
    Signature: AddressEmptyCode(address)
    """
    def __init__(self, address: str = None, **kwargs):
        details = {}
        if address:
            details['address'] = address
        
        message = "Calling a contract that has no bytecode"
        if address:
            message += f" (address: {address})"
        
        super().__init__(
            message,
            selector="0x9996b315",
            **{**details, **kwargs}
        )


class AddressInsufficientBalanceError(ContractError):
    """
    Raised when attempting to send native token with insufficient balance.
    Selector: 0xcd786059
    Signature: AddressInsufficientBalance(address)
    """
    def __init__(self, address: str = None, **kwargs):
        details = {}
        if address:
            details['address'] = address
        
        message = "Attempting to send native token with insufficient balance"
        if address:
            message += f" (address: {address})"
        
        super().__init__(
            message,
            selector="0xcd786059",
            **{**details, **kwargs}
        )


class EnforcedPauseError(ContractError):
    """
    Raised when function can only be called when the contract is unpaused.
    Selector: 0xd93c0665
    Signature: EnforcedPause()
    """
    def __init__(self, **kwargs):
        super().__init__(
            "Function can only be called when the contract is unpaused",
            selector="0xd93c0665",
            **kwargs
        )


class ExpectedPauseError(ContractError):
    """
    Raised when function can only be called when the contract is paused.
    Selector: 0x8dfc202b
    Signature: ExpectedPause()
    """
    def __init__(self, **kwargs):
        super().__init__(
            "Function can only be called when the contract is paused",
            selector="0x8dfc202b",
            **kwargs
        )


class FailedInnerCallError(ContractError):
    """
    Raised when a call to an address target failed. The target may have reverted.
    Selector: 0x1425ea42
    Signature: FailedInnerCall()
    """
    def __init__(self, **kwargs):
        super().__init__(
            "A call to an address target failed. The target may have reverted.",
            selector="0x1425ea42",
            **kwargs
        )


class InvalidNativeTransferError(ContractError):
    """
    Raised when native token transfer has failed.
    Selector: 0x79feaaea
    Signature: InvalidNativeTransfer()
    """
    def __init__(self, **kwargs):
        super().__init__(
            "Native token transfer has failed",
            selector="0x79feaaea",
            **kwargs
        )


class SafeERC20FailedOperationError(ContractError):
    """
    Raised when an operation with an ERC-20 token failed.
    Selector: 0x5274afe7
    Signature: SafeERC20FailedOperation(address)
    """
    def __init__(self, token: str = None, **kwargs):
        details = {}
        if token:
            details['token'] = token
        
        message = "An operation with an ERC-20 token failed"
        if token:
            message += f" (token: {token})"
        
        super().__init__(
            message,
            selector="0x5274afe7",
            **{**details, **kwargs}
        )


# ============================================================================
# Error Decoder
# ============================================================================

# Mapping of error selectors to exception classes
ERROR_SELECTOR_MAP = {
    "0xf4d678b8": InsufficientBalanceError,
    "0x71c4efed": SlippageExceededError,
    "0xfa463c69": SameTokenInAndOutError,
    "0x6da58071": MinimumOutputGreaterThanQuoteError,
    "0xf067d762": MinimumOutputIsZeroError,
    "0xdb4d141c": NativeDepositValueMismatchError,
    "0x9996b315": AddressEmptyCodeError,
    "0xcd786059": AddressInsufficientBalanceError,
    "0xd93c0665": EnforcedPauseError,
    "0x8dfc202b": ExpectedPauseError,
    "0x1425ea42": FailedInnerCallError,
    "0x79feaaea": InvalidNativeTransferError,
    "0x5274afe7": SafeERC20FailedOperationError,
}


def decode_contract_error(error_data: str) -> ContractError:
    """
    Decodes a contract error from the error data selector.
    
    Args:
        error_data: The error data hex string (e.g., '0xf4d678b8')
    
    Returns:
        ContractError: The appropriate exception instance
    
    Example:
        >>> error = decode_contract_error('0xf4d678b8')
        >>> raise error
        InsufficientBalanceError: Insufficient balance of input token
    """
    # Normalize the error data to lowercase and ensure it starts with 0x
    if not error_data.startswith('0x'):
        error_data = '0x' + error_data
    
    # Extract the selector (first 10 characters: 0x + 8 hex chars)
    selector = error_data[:10].lower()
    
    # Look up the exception class
    exception_class = ERROR_SELECTOR_MAP.get(selector)
    
    if exception_class:
        return exception_class()
    else:
        # Return a generic ContractError if the selector is unknown
        return ContractError(
            f"Unknown contract error with selector {selector}",
            selector=selector
        )
