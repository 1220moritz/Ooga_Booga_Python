from typing import List

from eth_typing import HexStr
from web3 import Web3
from web3.constants import MAX_INT, ADDRESS_ZERO
from web3.types import TxParams

from .custom_logger import get_logger
from .constants import BASE_URL, CHAIN_ID, BERA_ADDRESS, WBERA_ADDRESS, ERC20_ABI
from .http_client import HTTPClient
from .exceptions import decode_contract_error
from .models import (
    SwapParams,
    Token,
    AllowanceResponse,
    SwapResponse,
    PriceInfo,
    LiquiditySourcesResponse,
    SuccessfulSwapResponse,
    NoRouteResponse,
    TransactionReceipt,
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
        self.rpc_http_client = HTTPClient(
            headers={"Content-Type": "application/json"},
            max_retries=5,
            request_delay=1.0
        )

        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.account = self.w3.eth.account.from_key(private_key)
        self.address = self.account.address
        self._router_address = None

    async def _prepare_and_send_transaction(self, tx_params: TxParams) -> TransactionReceipt:
        """
        Prepares, signs, and sends a transaction, then waits for the receipt.

        Args:
            tx_params (TxParams): The transaction parameters.

        Returns:
            TransactionReceipt: The transaction receipt with statically-typed attributes.

        Raises:
            ValueError: If signing or sending fails
        """
        logger.info("Signing and sending transaction...")
        signed_tx = self.account.sign_transaction(tx_params)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        rcpt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        receipt = TransactionReceipt.from_web3(dict(rcpt))
        logger.info(
            f"Transaction complete: Transaction Hash: {receipt.transactionHash}, Status: {receipt.status}")
        return receipt


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
        gas_price = self.w3.eth.gas_price
        logger.debug(f"Gas price: {gas_price}")
        logger.debug(f"Value: {value}")

        try:
            gas = await self._estimate_gas_rpc(to, data, value)
        except Exception as e:
            logger.error(f"Gas estimation failed: {e}")
            raise e

        logger.debug(f"Gas: {gas}, Gas Price: {self.w3.eth.gas_price}, Value: {value}")
        return {
            "from": self.address,
            "to": to,
            "data": HexStr(data),
            "gas": gas,
            "value": value,
            "gasPrice": self.w3.eth.gas_price,
            "nonce": nonce,
            "chainId": CHAIN_ID,
        }

    async def _estimate_gas_rpc(self, to: str, data: str, value: int) -> int:
        """
        Estimates gas using a direct JSON-RPC call.

        Args:
            to (str): The recipient address.
            data (str): The transaction data.
            value (int): The transaction value.

        Returns:
            int: The estimated gas.
            
        Raises:
            ContractError: If the contract reverts with a known error
            ValueError: If the RPC call fails for other reasons
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_estimateGas",
            "params": [
                {
                    "from": self.address,
                    "to": to,
                    "data": data,
                    "value": hex(value)
                }
            ],
            "id": 1
        }

        response = await self.rpc_http_client.post(self.rpc_url, payload)
        
        if "error" in response:
            error_info = response['error']
            
            # Check if there's error data (contract revert)
            if 'data' in error_info and error_info['data']:
                error_data = error_info['data']
                logger.error(f"Gas estimation failed: RPC Error: {error_info}")
                
                # Decode and raise the specific contract error
                contract_error = decode_contract_error(error_data)
                raise contract_error
            else:
                # Generic RPC error without contract data
                raise ValueError(f"RPC Error: {error_info}")
        
        return int(response["result"], 16)

    def _get_erc20_contract(self, token_address: str):
        """
        Creates a Web3 contract instance for an ERC-20 token using the standard ABI.
        
        Args:
            token_address (str): The token address.
            
        Returns:
            Contract: The Web3 contract instance.
        """
        if not isinstance(token_address, str):
            raise ValueError("Token address must be a string")
        if not token_address.startswith('0x'):
            raise ValueError("Token address must be a valid Ethereum address starting with 0x")
        if len(token_address) != 42:
            raise ValueError("Token address must be 42 characters long (including 0x prefix)")
            
        return self.w3.eth.contract(address=token_address, abi=ERC20_ABI)

    async def _get_router_address(self) -> str:
        """
        Fetches the router address by performing a dummy swap if not already cached.

        Returns:
            str: The router address.
        """
        if self._router_address:
            return self._router_address

        # Dummy swap BERA -> wBERA to get router address
        swap_params = SwapParams(
            tokenIn=BERA_ADDRESS,
            tokenOut=WBERA_ADDRESS,
            amount=1,  # Smallest possible amount
            to=self.address
        )
        
        logger.debug("Fetching router address with dummy swap info...")
        try:
            swap_info = await self.get_swap_infos(swap_params)
            
            if isinstance(swap_info.response, SuccessfulSwapResponse):
                if swap_info.response.routerAddr:
                    self._router_address = swap_info.response.routerAddr
                    logger.info(f"Router address fetched: {self._router_address}")
                    return self._router_address
                elif swap_info.response.tx and swap_info.response.tx.to:
                     # Fallback to tx.to if routerAddr is missing but we have a tx
                    self._router_address = swap_info.response.tx.to
                    logger.info(f"Router address fetched from tx.to: {self._router_address}")
                    return self._router_address
            
            raise ValueError("Could not determine router address from dummy swap response")

        except Exception as e:
            logger.error(f"Failed to fetch router address: {e}")
            raise


    async def get_token_list(self) -> List[Token]:
        """
        Fetches a list of all available tokens.

        Returns:
            List[Token]: List of validated Token objects.
        """
        url = f"{self.base_url}/tokens"
        response_data = await self.http_client.get(url)
        return [Token(**token) for token in response_data]


    async def swap(self, swap_params: SwapParams, custom_nonce=None) -> TransactionReceipt:
        """
        Executes a token swap based on provided parameters.

        Args:
            swap_params (SwapParams): The swap parameters.
            custom_nonce (int, optional): Custom nonce for transaction ordering.

        Returns:
            TransactionReceipt: The transaction receipt. Use `receipt.success` or
                               `receipt.status` to check if the transaction succeeded.
        """
        if swap_params.tokenIn == swap_params.tokenOut:
            raise ValueError("Circular swaps not allowed: tokenIn and tokenOut must be different")

        url = f"{self.base_url}/swap"
        params = swap_params.model_dump(exclude_none=True)
        logger.debug(params)
        response_data = await self.http_client.get(url, params)
        logger.debug(response_data)
        swap_tx = SuccessfulSwapResponse(**response_data).tx

        value = 0 if swap_params.tokenIn != ADDRESS_ZERO else int(swap_tx.value)
        logger.debug(f"Value: {value}")
        tx_params = await self._build_transaction(
            to=swap_tx.to, data=swap_tx.data, value=value, custom_nonce=custom_nonce
        )
        logger.debug(tx_params)
        logger.info("Submitting swap...")
        return await self._prepare_and_send_transaction(tx_params)


    async def approve_allowance(self, token: str, amount: str = str(MAX_INT), custom_nonce=None) -> TransactionReceipt:
        """
        Approves an allowance for a given token using direct ERC-20 contract call.

        Args:
            token (str): The token address.
            amount (str, optional): The amount to approve. Defaults to MAX_INT.
            custom_nonce (int, optional): Custom nonce for transaction ordering.

        Returns:
            TransactionReceipt: The transaction receipt. Use `receipt.success` or
                               `receipt.status` to check if the transaction succeeded.
        """
        router_address = await self._get_router_address()
        contract = self._get_erc20_contract(token)
        
        # Build transaction data
        tx_data = contract.encode_abi(
            "approve", 
            args=[router_address, int(str(amount), 0)]
        )
        
        tx_params = await self._build_transaction(
            to=token, 
            data=tx_data, 
            custom_nonce=custom_nonce
        )

        logger.info(f"Approving token {token} for spender {router_address} with amount {amount}...")
        return await self._prepare_and_send_transaction(tx_params)


    async def get_token_allowance(self, from_address: str, token: str) -> AllowanceResponse:
        """
        Fetches the allowance of a token for a specific address using direct ERC-20 contract call.

        Args:
            from_address (str): The address to check allowance for.
            token (str): The token address.

        Returns:
            AllowanceResponse: The allowance details.
        """
        if token == ADDRESS_ZERO:
            return AllowanceResponse(allowance=str(MAX_INT))
            
        router_address = await self._get_router_address()
        contract = self._get_erc20_contract(token)
        
        # Call allowance function
        allowance = contract.functions.allowance(from_address, router_address).call()
        
        return AllowanceResponse(allowance=str(allowance))


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
