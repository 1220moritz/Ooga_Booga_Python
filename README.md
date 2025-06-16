# Ooga Booga Python Client

[![PyPI](https://img.shields.io/pypi/v/Ooga-Booga-Python)](https://pypi.org/project/Ooga-Booga-Python/) 
[![Downloads](https://static.pepy.tech/badge/Ooga-Booga-Python)](https://pepy.tech/project/Ooga-Booga-Python) 
[![Tests](https://github.com/1220moritz/Ooga_Booga_Python/actions/workflows/tests.yml/badge.svg)](https://github.com/1220moritz/Ooga_Booga_Python/actions/workflows/tests.yml)  

[GitHub Repository](https://github.com/1220moritz/Ooga_Booga_Python)  
[PyPI Package](https://pypi.org/project/Ooga-Booga-Python/)

The **Ooga Booga Python Client** is a wrapper for the [Ooga Booga API V1](https://docs.oogabooga.io/), a powerful DEX aggregation and smart order routing REST API built to integrate Berachain's liquidity into your DApp or protocol. This client allows you to interact with Berachain's liquidity sources, including AMMs, bonding curves, and order books, to execute the best trades with minimal price impact.

For more details on the API and its capabilities, refer to the official [Ooga Booga API Documentation](https://docs.oogabooga.io/).

## Features

- **Find the Best Rates**: Get optimal real-time prices for your trades by leveraging Ooga Booga's liquidity aggregation.
- **Simplified Integration**: A single API integration grants access to all liquidity sources on Berachain, saving you development time.
- **Optimal Trade Execution**: Perform efficient trades with minimized price impact and maximum returns for your users.
- **Enhanced Security**: Execute trades securely via Ooga Booga’s smart contract, which wraps each transaction.
- **Asynchronous API** calls using `aiohttp` for smooth, non-blocking operations.

## Features

- Fetch token lists and prices
- Approve token allowances
- Query token allowances
- Perform token swaps
- Retrieve liquidity sources
- Comprehensive error handling
- Asynchronous API calls using `aiohttp`

## Table of Contents

- [Installation](#installation)
- [Setup](#setup)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)

---

## Installation

To install the Ooga-Booga-Python package, use pip. Run the following command in your terminal:

```bash
pip install Ooga-Booga-Python
```

To upgrade the package to the latest version, run:

```bash
pip install --upgrade Ooga-Booga-Python
```

If you prefer installing directly from the GitHub repository, use:

```bash
pip install git+https://github.com/1220moritz/Ooga_Booga_Python.git
```

---


## Setup

1. Copy the `example_env.env` file to `.env`:

```bash
cp tests/example_env.env .env
```

2. Add your API key and private key:

```plaintext
OOGA_BOOGA_API_KEY="your-api-key"
PRIVATE_KEY="your-private-key"
```

3. Install dependencies:

```bash
pip install -e ".[dev]"
```

---

## Usage

Here’s how to use the **Ooga Booga Python Client**, demonstrating various functionalities from a single client initialization:

```python
from ooga_booga_python.client import OogaBoogaClient
from ooga_booga_python.models import SwapParams
import asyncio
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

async def main():
    # Initialize the client once for all operations
    client = OogaBoogaClient(
        api_key=os.getenv("OOGA_BOOGA_API_KEY"),
        private_key=os.getenv("PRIVATE_KEY")
    )

    print("--- Initializing Client and Fetching Token List ---")
    await fetch_token_list_example(client)

    print("\n--- Performing a Token Swap ---")
    await perform_swap_example(client)

    print("\n--- Getting Token Prices ---")
    await fetch_prices_example(client)

async def fetch_token_list_example(client):
    """
    Fetches and prints the list of available tokens.
    """
    try:
        tokens = await client.get_token_list()
        for token in tokens:
            print(f"Name: {token.name}, Symbol: {token.symbol}")
    except Exception as e:
        print(f"Failed to fetch token list: {e}")

async def perform_swap_example(client):
    """
    Demonstrates how to perform a token swap.
    """
    swap_params = SwapParams(
        tokenIn="0xTokenInAddress", # Replace with actual token address
        amount=1000000000000000000,  # 1 token in wei
        tokenOut="0xTokenOutAddress", # Replace with actual token address
        to="0xYourWalletAddress", # Replace with your wallet address
        slippage=0.02,
    )
    try:
        transaction_hash = await client.swap(swap_params)
        print(f"Swap successful! Transaction Hash: {transaction_hash}")
    except Exception as e:
        print(f"Swap failed: {e}")

async def fetch_prices_example(client):
    """
    Fetches and prints the prices of available tokens.
    """
    try:
        prices = await client.get_token_prices()
        for price in prices:
            print(f"Token: {price.address}, Price: {price.price}")
    except Exception as e:
        print(f"Failed to fetch token prices: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## API Reference

### `OogaBoogaClient`

#### Initialization

```python
client = OogaBoogaClient(api_key: str, private_key: str, rpc_url: str = "https://rpc.berachain.com/")
```

- **`api_key`**: Your API key for authentication.
- **`private_key`**: Your private key for signing transactions.
- **`rpc_url`**: (Optional) RPC URL for blockchain interaction.

#### Methods

1. **`get_token_list()`**  
   Fetches the list of available tokens.

2. **`get_token_prices()`**  
   Fetches the current prices of tokens.

3. **`get_liquidity_sources()`**  
   Fetches all available liquidity sources.

4. **`swap(swap_params: SwapParams)`**  
   Performs a token swap using the provided parameters.

5. **`approve_allowance(token: str, amount: str = MAX_INT)`**  
   Approves a token allowance for the router.

6. **`get_token_allowance(from_address: str, token: str)`**  
   Fetches the allowance of a token for a specific address.

---

## Testing

The package uses `pytest` for testing. To run the tests:

1. Install test dependencies:

```bash
pip install -e ".[dev]"
```

2. Run the tests:

```bash
pytest tests/
```

---

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your fork
5. Open a pull request

---

## License

This project is licensed under the [MIT License](LICENSE).