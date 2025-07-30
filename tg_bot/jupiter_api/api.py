import os
import requests
import base58
import base64
import json
from requests import JSONDecodeError
from solders.solders import Keypair, VersionedTransaction,Mint
from spl.token._layouts import MINT_LAYOUT
from solana.rpc.api import Client, Pubkey

def get_decimals(mint: str):
    http_client = Client("https://api.mainnet-beta.solana.com")
    addr = Pubkey.from_string(mint)
    info = http_client.get_account_info(addr)
    decimals = MINT_LAYOUT.parse(info.value.data).decimals
    # All token data
    #token_data = MINT_LAYOUT.parse(info.value.data)
    return int(decimals)

def order(inputMint: str, outputMint: str, amount: int):
    # Create a keypair wallet from your private key
    with(open("config.json", 'r')) as f:
        PRIVATE_KEY = json.load(f)['PRIVATE_KEY']

    private_key_bytes = base58.b58decode(PRIVATE_KEY)
    wallet = Keypair.from_bytes(private_key_bytes)
    # Fetch a quote to swap WSOL (Wrapped SOL) to USDC tokens
    order_params = {
        "inputMint": inputMint,  
        "outputMint": outputMint,
        "amount": int(amount*10**get_decimals(inputMint)),  # Convert unit
        "taker": str(wallet.pubkey()),  # Wallet public key
    }
    #print(int(amount*10**get_decimals(inputMint)))

    order_response = requests.get(
        "https://lite-api.jup.ag/ultra/v1/order", params=order_params
    )

    if order_response.status_code != 200:
        try:
            print(f"Error fetching order: {order_response.json()}")
        except JSONDecodeError as e:
            print(f"Error fetching order: {order_response.json()}")
        finally:
            exit()

    order_data = order_response.json()

    print("Order response:", order_data)

    # Get Raw Transaction
    swap_transaction_base64 = order_data["transaction"]
    swap_transaction_bytes = base64.b64decode(swap_transaction_base64)
    raw_transaction = VersionedTransaction.from_bytes(swap_transaction_bytes)

    # Sign Transaction
    account_keys = raw_transaction.message.account_keys
    wallet_index = account_keys.index(wallet.pubkey())

    signers = list(raw_transaction.signatures)
    signers[wallet_index] = wallet

    signed_transaction = VersionedTransaction(raw_transaction.message, signers)
    serialized_signed_transaction = base64.b64encode(bytes(signed_transaction)).decode(
        "utf-8"
    )

    # Execute the order transaction
    execute_request = {
        "signedTransaction": serialized_signed_transaction,
        "requestId": order_data["requestId"],
    }

    execute_response = requests.post(
        "https://lite-api.jup.ag/ultra/v1/execute", json=execute_request
    )

    if execute_response.status_code == 200:
        error_data = execute_response.json()
        signature = error_data["signature"]

        if error_data["status"] == "Success":
            print(f"Transaction sent successfully! Signature: {signature}")
            print(f"View transaction on Solscan: https://solscan.io/tx/{signature}")
        else:
            error_code = error_data["code"]
            error_message = error_data["error"]

            print(f"Transaction failed! Signature: {signature}")
            print(f"Custom Program Error Code: {error_code}")
            print(f"Message: {error_message}")
            print(f"View transaction on Solscan: https://solscan.io/tx/{signature}")
    else:
        print(f"Error executing order: {execute_response.json()}")



def get_balance(address: str)->dict:

    url = f"https://lite-api.jup.ag/ultra/v1/balances/{address}"

    payload = {}
    headers = {
    'Accept': 'application/json'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print("error1111")


def get_token_data_by_token_address(token_address: str)->dict:

    url = f"https://lite-api.jup.ag/ultra/v1/search?query={token_address}"

    headers = {
    'Accept': 'application/json'
    }

    response = requests.request("GET", url, headers=headers)
    #print(response.text)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print("error222322")

if __name__ == "__main__":
    #get_token_data_by_token_address()
    #get_balance("HbjRwJqFQJxEEhczcPznd8BJci3wj9fRzAPsP8bSuvCN")
    #order("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", "27G8MtK7VtTcCHkpASjSDdkWWYfoqT6ggEuKidVJidD4",0.1)
    ...