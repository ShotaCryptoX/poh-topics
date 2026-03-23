#!/usr/bin/env python3
"""
mint_ticket.py — Mint a PoHTicket NFT

Usage:
    python mint_ticket.py

Environment variables (set in .env file):
    PRIVATE_KEY       : Private key (with or without 0x)
    RPC_URL           : Base Mainnet RPC endpoint
    OPEPE_ADDRESS     : OPEPE Token Contract Address
    TICKET_ADDRESS    : PoHTicket Contract Address
    POHGAME_ADDRESS   : PoHGame Contract Address
"""

import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3

# Load .env
load_dotenv(Path(__file__).parent.parent / ".env")

PRIVATE_KEY     = os.environ["PRIVATE_KEY"]
RPC_URL         = os.environ.get("RPC_URL", "https://mainnet.base.org")
OPEPE_ADDRESS   = os.environ.get("OPEPE_ADDRESS",   "0x06AC76da01657e40a6724E2035dDAdC6f57eD034")
TICKET_ADDRESS  = os.environ.get("TICKET_ADDRESS",  "0x8Ad615dA799E4c233028b1643030F802AA857f34")

# Load ABI
ABI_DIR = Path(__file__).parent.parent / "abi"

def load_abi(name: str):
    path = ABI_DIR / f"{name}.json"
    with open(path) as f:
        return json.load(f)

def main():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print("❌ RPC connection failed:", RPC_URL)
        sys.exit(1)

    account = w3.eth.account.from_key(PRIVATE_KEY)
    my_address = account.address
    print(f"👛 Address: {my_address}")

    opepe  = w3.eth.contract(address=Web3.to_checksum_address(OPEPE_ADDRESS),  abi=load_abi("MockOPEPE"))
    ticket = w3.eth.contract(address=Web3.to_checksum_address(TICKET_ADDRESS), abi=load_abi("PoHTicket"))

    # Get ticket price
    ticket_price = ticket.functions.ticketPrice().call()
    print(f"🎫 Ticket price: {ticket_price} OPEPE wei")

    # Check OPEPE balance
    balance = opepe.functions.balanceOf(my_address).call()
    print(f"💰 OPEPE balance: {balance} wei")
    if balance < ticket_price:
        print(f"❌ Insufficient OPEPE. Required: {ticket_price}, Current: {balance}")
        sys.exit(1)

    # Use EIP-1559 gas price for better compatibility on Base
    priority_fee = w3.to_wei(0.01, 'gwei')
    base_fee = w3.eth.get_block('latest')['baseFeePerGas']
    max_fee = base_fee + priority_fee

    # Approve
    print("🔑 Sending OPEPE approve transaction...")
    nonce = w3.eth.get_transaction_count(my_address, 'pending') # use pending to overwrite if stuck
    
    # Increase priority fee slightly to replace stuck tx
    priority_fee_replace = w3.to_wei(2, 'gwei')
    max_fee_replace = base_fee + priority_fee_replace
    
    tx = opepe.functions.approve(
        Web3.to_checksum_address(TICKET_ADDRESS),
        ticket_price
    ).build_transaction({
        "from": my_address,
        "nonce": nonce,
        "gas": 100_000,
        "maxFeePerGas": max_fee_replace,
        "maxPriorityFeePerGas": priority_fee_replace,
        "chainId": w3.eth.chain_id,
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"✅ Approve successful | txHash: {tx_hash.hex()}")

    # Mint
    print("🎫 Sending PoHTicket.mint() transaction...")
    nonce = nonce + 1
    tx = ticket.functions.mint().build_transaction({
        "from": my_address,
        "nonce": nonce,
        "gas": 200_000,
        "maxFeePerGas": max_fee_replace,
        "maxPriorityFeePerGas": priority_fee_replace,
        "chainId": w3.eth.chain_id,
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt["status"] == 1:
        print(f"✅ Ticket Mint successful! | txHash: {tx_hash.hex()}")
        print(f"   BlockExplorer: https://basescan.org/tx/{tx_hash.hex()}")
    else:
        print(f"❌ Mint failed | txHash: {tx_hash.hex()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
