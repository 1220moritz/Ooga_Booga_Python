from typing import List

from eth_typing import HexStr
from web3 import Web3
from web3.constants import MAX_INT, ADDRESS_ZERO
from web3.exceptions import ContractCustomError
from web3.types import TxParams

from .custom_logger import get_logger
from .constants import BASE_URL, CHAIN_ID
from .http_client import HTTPClient
from .models import (
    SwapParams,
    Token,
    ApproveResponse,
    AllowanceResponse,
    SwapResponse,
    PriceInfo,
    LiquiditySourcesResponse, SuccessfulSwapResponse, NoRouteResponse,
)

# Logging setup
logger = get_logger(__name__)


class OogaBoogaClient:
    """
    A client for interacting with the Ooga Booga API.

    Args:
        api_key (str): API key for authentication.
        max_retries (int): Maximum number of retries for requests.
        request_delay (int): Delay in seconds between retries.

    Attributes:
        api_key (str): API key for authentication.
        private_key (str): Private key for signing transactions.
        rpc_url (str): RPC URL for blockchain interactions.
        max_retries (int): Maximum number of retries for requests.
        request_delay (int): Delay in seconds between retries.
        base_url (str): Base URL for the API.
        headers (dict): Headers used for API requests.
        w3 (Web3): Web3 instance for blockchain interaction.
        account (LocalAccount): Ethereum account derived from the private key.
        address (str): Address of the Ethereum account.
    """
    def __init__(self, api_key: str, private_key: str, rpc_url: str = "https://rpc.berachain.com/", max_retries: int = 5, request_delay: int = 5):
        if not api_key:
            raise ValueError("API key is required.")
        if not rpc_url:
            raise ValueError("Provider URL is required.")
        if not private_key:
            raise ValueError("Private key is required.")

        self.api_key = api_key
        self.private_key = private_key
        self.rpc_url = rpc_url
        self.max_retries = max_retries
        self.request_delay = request_delay
        self.base_url = BASE_URL
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        self.http_client = HTTPClient(
            headers=self.headers,
            max_retries=5,
            request_delay=1.0
        )

        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.account = self.w3.eth.account.from_key(private_key)
        self.address = self.account.address

    async def _prepare_and_send_transaction(self, tx_params: TxParams) -> dict:
        """
        Prepares, signs, and sends a transaction, then waits for the receipt.

        Args:
            tx_params (TxParams): The transaction parameters.

        Returns:
            dict: The transaction receipt.

        Raises:
            ValueError: If signing or sending fails
        """
        logger.info("Signing and sending transaction...")
        signed_tx = self.account.sign_transaction(tx_params)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        rcpt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        logger.info(
            f"Transaction complete: Transaction Hash: 0x{rcpt['transactionHash'].hex()}, Status: {rcpt['status']}")
        return rcpt


    async def _build_transaction(self, to: str, data: str, value: int = 0, custom_nonce=None) -> TxParams:
        """
        Builds a transaction dictionary with common parameters.

        Args:
            to (str): The recipient address.
            data (str): The transaction data.
            value (int, optional): The transaction value. Defaults to 0.

        Returns:
            TxParams: The transaction parameters.
        """
        nonce = custom_nonce or self.w3.eth.get_transaction_count(self.address)
        try:
            gas = self.w3.eth.estimate_gas({"from": self.address, "to": to, "data": HexStr(data)})
        except ContractCustomError as e:
            # Extract the error selector (first 4 bytes)
            error_data = e.args[0] if e.args else "Unknown"
            logger.error(f"Contract execution would fail. Error selector: {error_data}")

            # You can add specific error decoding based on known selectors
            if error_data == "0xf4d678b8":
                raise ValueError(
                    "Swap would fail - possible reasons: insufficient balance, slippage too high, or invalid token pair")
            else:
                raise ValueError(f"Contract execution would fail with error: {error_data}")

        except ValueError as e:
            logger.error(f"Gas estimation failed: {e}")
            raise e

        return {
            "from": self.address,
            "to": to,
            "data": HexStr(data),
            "gas": gas,
            "value": Web3.to_wei(value, "wei"),
            "gasPrice": self.w3.eth.gas_price,
            "nonce": nonce,
            "chainId": CHAIN_ID,
        }


    async def get_token_list(self) -> List[Token]:
        """
        Fetches a list of all available tokens.

        Returns:
            List[Token]: List of validated Token objects.
        """
        url = f"{self.base_url}/tokens"
        response_data = await self.http_client.get(url)
        return [Token(**token) for token in response_data]


    async def swap(self, swap_params: SwapParams, custom_nonce=None) -> None:
        """
        Executes a token swap based on provided parameters.

        Args:
            swap_params (SwapParams): The swap parameters.
            custom_nonce (int, optional): Custom nonce for transaction ordering.
        """
        url = f"{self.base_url}/swap"
        params = swap_params.model_dump(exclude_none=True)
        print(params)
        response_data = await self.http_client.get(url, params)
        print(response_data)
        swap_tx = SuccessfulSwapResponse(**response_data).tx

        value = 0 if swap_params.tokenIn != ADDRESS_ZERO else swap_tx.value
        tx_params = await self._build_transaction(
            to=swap_tx.to, data=swap_tx.data, value=value, custom_nonce=custom_nonce
        )

        logger.info("Submitting swap...")
        await self._prepare_and_send_transaction(tx_params)


    async def approve_allowance(self, token: str, amount: str = MAX_INT, custom_nonce=None) -> None:
        """
        Approves an allowance for a given token.

        Args:
            token (str): The token address.
            amount (str, optional): The amount to approve. Defaults to MAX_INT.
            custom_nonce (int, optional): Custom nonce for transaction ordering.
        """
        url = f"{self.base_url}/approve"
        params = {"token": token, "amount": amount}
        response_data = await self.http_client.get(url, params)
        approve_tx = ApproveResponse(**response_data).tx

        tx_params = await self._build_transaction(to=approve_tx.to, data=approve_tx.data, custom_nonce=custom_nonce)

        logger.info(f"Approving token {token} with amount {amount}...")
        await self._prepare_and_send_transaction(tx_params)


    async def get_token_allowance(self, from_address: str, token: str) -> AllowanceResponse:
        """
        Fetches the allowance of a token for a specific address.

        Args:
            from_address (str): The address to check allowance for.
            token (str): The token address.

        Returns:
            AllowanceResponse: The allowance details.
        """

        if token == ADDRESS_ZERO:
            return AllowanceResponse(allowance=str(MAX_INT))

        url = f"{self.base_url}/approve/allowance"
        params = {"from": from_address, "token": token}
        response_data = await self.http_client.get(url, params)
        return AllowanceResponse(**response_data)


    async def get_token_prices(self) -> List[PriceInfo]:
        """
        Fetches the current prices of tokens.

        Returns:
            List[PriceInfo]: A list of price information for tokens.
        """
        url = f"{self.base_url}/prices"
        response_data = await self.http_client.get(url)
        return [PriceInfo(**price) for price in response_data]


    async def get_liquidity_sources(self) -> List[str]:
        """
        Fetches all available liquidity sources.

        Returns:
            List[str]: List of liquidity source names.
        """
        url = f"{self.base_url}/liquidity-sources"
        response_data = await self.http_client.get(url)
        parsed = LiquiditySourcesResponse.model_validate(response_data)
        return parsed.root


    async def get_swap_infos(self, swap_params: SwapParams) -> SwapResponse:
        """
        Prepares swap information and routes the swap.

        Args:
            swap_params (SwapParams): Parameters for the swap.

        Returns:
            SwapResponse: The response from the swap endpoint.
        """
        url = f"{self.base_url}/swap/"
        params = swap_params.model_dump(exclude_none=True)
        response_data = await self.http_client.get(url, params)

        if response_data.get("status") == "NoWay":
            return SwapResponse(response=NoRouteResponse(**response_data))
        else:
            return SwapResponse(response=SuccessfulSwapResponse(**response_data))
