from typing import List, Union, Optional
from pydantic import BaseModel, RootModel, field_validator, Field


class SwapParams(BaseModel):
    tokenIn: str
    amount: int
    tokenOut: str
    to: str
    slippage: float = Field(default=0.02, description="Slippage tolerance (0 < slippage <= 1)")
    liquidity_sources: Optional[List[str]] = None

    @field_validator('slippage')
    @classmethod
    def validate_slippage(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Slippage must be greater than 0")
        if v > 1.0:
            raise ValueError(f"Slippage too high: {v}. Must be ≤ 1.0 (100%). Did you mean {v/100}?")
        return v

    @field_validator('tokenIn')
    @classmethod
    def validate_token_in(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("tokenIn must be a string")
        if not v.startswith('0x'):
            raise ValueError("tokenIn must be a valid Ethereum address starting with 0x")
        if len(v) != 42:
            raise ValueError("tokenIn must be 42 characters long (including 0x prefix)")
        return v

    @field_validator('tokenOut')
    @classmethod
    def validate_token_out(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("tokenOut must be a string")
        if not v.startswith('0x'):
            raise ValueError("tokenOut must be a valid Ethereum address starting with 0x")
        if len(v) != 42:
            raise ValueError("tokenOut must be 42 characters long (including 0x prefix)")
        return v

    @field_validator('to')
    @classmethod
    def validate_to(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("to must be a string")
        if not v.startswith('0x'):
            raise ValueError("to must be a valid Ethereum address starting with 0x")
        if len(v) != 42:
            raise ValueError("to must be 42 characters long (including 0x prefix)")
        return v

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v

class Token(BaseModel):
    """
    Pydantic model for a token object.

    Attributes:
        address (str): EVM Address in 0x format.
        name (str): Name of the token.
        symbol (str): Symbol of the token.
        decimals (int): Number of decimals for the token.
        tokenURI (HttpUrl): URI for the token's metadata.
    """
    address: str
    name: str
    symbol: str
    decimals: int
    tokenURI: str


class ApproveTransaction(BaseModel):
    """
    Pydantic model for the transaction details of an approval.

    Attributes:
        to (str): The EVM address to send the approval to.
        data (str): Hex-encoded transaction data.
    """
    to: str
    data: str


class ApproveResponse(BaseModel):
    """
    Pydantic model for the response of an approval request.

    Attributes:
        tx (ApproveTransaction): The transaction details for the approval.
    """
    tx: ApproveTransaction


class AllowanceResponse(BaseModel):
    """
    Pydantic model for the response of an allowance request.

    Attributes:
        allowance (str): The allowance for the router, represented as a string.
    """
    allowance: str


class SwapToken(BaseModel):
    """
    Represents a token used in the swap route.

    Attributes:
        address (str): The EVM address of the token.
        name (str): The name of the token.
        symbol (str): The symbol of the token.
        decimals (int): The number of decimals for the token.
    """
    address: str
    name: str
    symbol: str
    decimals: int


class SwapRoute(BaseModel):
    """
    Represents a single route in the swap.

    Attributes:
        poolAddress (str): The address of the pool.
        poolType (str): The type of the pool.
        poolName (str): The name of the pool.
        liquiditySource (str): The source of liquidity.
        poolFee (float): The fee for the pool.
        tokenFrom (int): The index of the from-token in the `tokens` array.
        tokenTo (int): The index of the to-token in the `tokens` array.
        share (int): The share of the route.
        assumedAmountIn (str): The assumed input amount.
        assumedAmountOut (str): The assumed output amount.
    """
    poolAddress: str
    poolType: str
    poolName: str
    liquiditySource: str
    poolFee: float
    tokenFrom: int
    tokenTo: int
    share: float
    assumedAmountIn: str
    assumedAmountOut: str


class SwapTx(BaseModel):
    """
    Represents the transaction details for the swap.

    Attributes:
        to (str): The recipient's EVM address.
        data (str): The transaction data in hex format.
        value (str): The transaction value.
    """
    to: str
    data: str
    value: str


class SwapTokenInfo(BaseModel):
    """
    Represents the swap token information.

    Attributes:
        inputToken (str): The input token address.
        inputAmount (str): The input amount.
        outputToken (str): The output token address.
        outputQuote (str): The output quote.
        outputMin (str): The minimum output amount.
        outputReceiver (str): The output receiver address.
    """
    inputToken: str
    inputAmount: str
    outputToken: str
    outputQuote: str
    outputMin: str
    outputReceiver: str


class RouterParams(BaseModel):
    """
    Represents the parameters for the swap router.

    Attributes:
        swapTokenInfo (dict): Information about the swap tokens.
        pathDefinition (str): Path definition.
        executor (str): Executor's address.
        referralCode (Union[str, int]): Referral code.
        value (Optional[str]): Optional transaction value.
    """
    swapTokenInfo: SwapTokenInfo
    pathDefinition: str
    executor: str
    referralCode: Union[str, int]
    value: Optional[str] = None


class SuccessfulSwapResponse(BaseModel):
    """
    Represents a successful swap response.

    Attributes:
        status (str): The status of the swap ("Success" or "Partial").
        tokenFrom (int): Index of the input token in the `tokens` array.
        tokenTo (int): Index of the output token in the `tokens` array.
        price (float): The price of the swap.
        priceImpact (float): The price impact of the swap.
        tokens (List[SwapToken]): List of tokens involved in the swap.
        amountIn (str): Input amount.
        amountOutFee (str): Output amount after fees.
        assumedAmountOut (str): Assumed output amount.
        route (Optional[List[SwapRoute]]): The route details for the swap.
        tx (Optional[SwapTx]): Transaction details.
        routerAddr (Optional[str]): The router's EVM address.
        routerParams (Optional[RouterParams]): Additional router parameters.
    """
    status: str
    tokenFrom: int
    tokenTo: int
    price: float
    priceImpact: float
    amountIn: str
    amountOutFee: str
    assumedAmountOut: str
    tokens: List[SwapToken]
    route: Optional[List[SwapRoute]] = None
    tx: Optional[SwapTx] = None
    routerAddr: Optional[str] = None
    routerParams: Optional[RouterParams] = None


class NoRouteResponse(BaseModel):
    """
    Represents a response when no route is available.

    Attributes:
        status (str): The status ("NoWay").
    """
    status: str


class SwapResponse(BaseModel):
    """
    Wraps all possible swap responses.

    Attributes:
        response (Union[SuccessfulSwapResponse, NoRouteResponse]): The swap response.
    """
    response: Union[SuccessfulSwapResponse, NoRouteResponse]


class PriceInfo(BaseModel):
    """
    Represents the price information for a token.

    Attributes:
        address (str): The EVM address of the token.
        price (float): The price of the token.
    """
    address: str
    price: float


class LiquiditySourcesResponse(RootModel[List[str]]):
    """
    A Pydantic v2 RootModel that validates a JSON array of liquidity sources as a list of strings.
    This allows for new liquidity sources to be added without requiring model updates.
    """