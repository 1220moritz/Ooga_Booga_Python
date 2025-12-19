# Ooga Booga Python Client

[![PyPI](https://img.shields.io/pypi/v/Ooga-Booga-Python)](https://pypi.org/project/Ooga-Booga-Python/)
[![Downloads](https://static.pepy.tech/badge/Ooga-Booga-Python)](https://pepy.tech/project/Ooga-Booga-Python)
[![Tests](https://github.com/1220moritz/Ooga_Booga_Python/actions/workflows/tests.yml/badge.svg)](https://github.com/1220moritz/Ooga_Booga_Python/actions/workflows/tests.yml)

[GitHub Repository](https://github.com/1220moritz/Ooga_Booga_Python) | [PyPI Package](https://pypi.org/project/Ooga-Booga-Python/)

The **Ooga Booga Python Client** is a wrapper for the [Ooga Booga API V1](https://docs.oogabooga.io/), a powerful DEX aggregation and smart order routing REST API built to integrate Berachain's liquidity into your DApp or protocol. This client allows you to interact with Berachain's liquidity sources, including AMMs, bonding curves, and order books, to execute the best trades with minimal price impact.

For more details on the API and its capabilities, refer to the official [Ooga Booga API Documentation](https://docs.oogabooga.io/).

## Features

- **Optimal Trade Execution**: Get real-time prices and execute trades with minimized price impact by leveraging liquidity aggregation.
- **Simplified Integration**: Single API access to all liquidity sources on Berachain.
- **Token Management**: Fetch token lists, prices, and query or approve allowances.
- **Enhanced Security**: Trades are executed via Ooga Booga's smart contract.
- **Async Support**: Built with `aiohttp` for high-performance asynchronous calls.
- **Custom Error Decoding**: Decode custom errors from smart contracts for better error handling.

## Table of Contents

- [Installation](#installation)
- [Setup](#setup)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)

---

## Installation

You can install the package using your preferred package manager.

### Package Manager

| Manager | Install Command | Upgrade Command |
| :--- | :--- | :--- |
| **Poetry** | `poetry add Ooga-Booga-Python` | `poetry update Ooga-Booga-Python` |
| **uv** | `uv add Ooga-Booga-Python` | `uv add Ooga-Booga-Python` |
| **pip** | `pip install Ooga-Booga-Python` | `pip install --upgrade Ooga-Booga-Python` |

### From Source

To install directly from the repository:

```
# Poetry
poetry add git+https://github.com/1220moritz/Ooga_Booga_Python.git

# uv
uv add git+https://github.com/1220moritz/Ooga_Booga_Python.git

# pip
pip install git+https://github.com/1220moritz/Ooga_Booga_Python.git
```

---

## Setup

1. **Environment Configuration**  
   Copy the example environment file:
   ```
   cp tests/example_env.env .env
   ```

2. **Credentials**  
   Add your keys to `.env`:
   ```
   OOGA_BOOGA_API_KEY="your-api-key"
   PRIVATE_KEY="your-private-key"
   ```

3. **Dev Dependencies** (Optional for contributors)
   ```
   # Poetry
   poetry install --with dev

   # uv
   uv sync --extra dev

   # pip
   pip install -e ".[dev]"
   ```

---

## Usage

Here is a complete example initializing the client and performing standard operations.

```
import asyncio
import os
from dotenv import load_dotenv
from ooga_booga_python.client import OogaBoogaClient
from ooga_booga_python.models import SwapParams

# Load environment variables
load_dotenv()

async def main():
    # Initialize the client
    client = OogaBoogaClient(
        api_key=os.getenv("OOGA_BOOGA_API_KEY"),
        private_key=os.getenv("PRIVATE_KEY")
    )

    print("--- Fetching Token List ---")
    await fetch_token_list_example(client)

    print("\n--- Getting Token Prices ---")
    await fetch_prices_example(client)

    print("\n--- Performing a Token Swap ---")
    await perform_swap_example(client)

async def fetch_token_list_example(client):
    try:
        tokens = await client.get_token_list()
        for token in tokens[:5]: # Print first 5 for brevity
            print(f"Name: {token.name}, Symbol: {token.symbol}")
    except Exception as e:
        print(f"Error: {e}")

async def fetch_prices_example(client):
    try:
        prices = await client.get_token_prices()
        for price in prices[:5]:
            print(f"Token: {price.address}, Price: {price.price}")
    except Exception as e:
        print(f"Error: {e}")

async def perform_swap_example(client):
    swap_params = SwapParams(
        tokenIn="0xTokenInAddress",    # Replace with actual address
        amount=1000000000000000000,    # 1 token in wei
        tokenOut="0xTokenOutAddress",  # Replace with actual address
        to="0xYourWalletAddress",      # Your wallet
        slippage=0.02,
    )
    try:
        receipt = await client.swap(swap_params)
        if receipt.success:
            print(f"Swap successful! Hash: {receipt.transactionHash}")
        else:
            print(f"Swap failed on-chain! Hash: {receipt.transactionHash}")
    except Exception as e:
        print(f"Swap failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## API Reference

### `OogaBoogaClient`

#### Initialization
```
client = OogaBoogaClient(
    api_key: str, 
    private_key: str, 
    rpc_url: str = "https://rpc.berachain.com/"
)
```

#### Core Methods

| Method | Description |
| :--- | :--- |
| `get_token_list()` | Returns list of available tokens. |
| `get_token_prices()` | Returns current token prices. |
| `get_liquidity_sources()` | Returns all available liquidity sources. |
| `swap(swap_params)` | Executes a token swap, returns `TransactionReceipt`. |
| `approve_allowance(token, amount)` | Approves token allowance, returns `TransactionReceipt`. |
| `get_token_allowance(address, token)` | Checks allowance for a specific address/token. |

---

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your fork
5. Open a pull request

**Running Tests:**
```
# Poetry
poetry install --with dev && poetry run pytest

# uv
uv sync --extra dev && uv run pytest
```

**Running Linter:**
```
uv sync --extra dev && uv run lint
```

---

## License

This project is licensed under the [MIT License](LICENSE).
