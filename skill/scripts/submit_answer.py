#!/usr/bin/env python3
"""
submit_answer.py — Submit an answer via PoHGame.submit()

Usage:
    python submit_answer.py --round 20260304 --ticket 1 --answer "Answer text"
    python submit_answer.py --round 20260304 --ticket 1 --answer "Answer text" --dry-run

Environment variables (set in .env file):
    PRIVATE_KEY       : Private key (with or without 0x)
    RPC_URL           : Base Mainnet RPC endpoint
    POHGAME_ADDRESS   : PoHGame Contract Address
    TICKET_ADDRESS    : PoHTicket Contract Address
"""

import os
import json
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3
from eth_hash.auto import keccak

# Load .env
load_dotenv(Path(__file__).parent.parent / ".env")

PRIVATE_KEY     = os.environ["PRIVATE_KEY"]
RPC_URL         = os.environ.get("RPC_URL",          "https://mainnet.base.org")
POHGAME_ADDRESS = os.environ.get("POHGAME_ADDRESS",  "0x0B69F81aa064BdE21F0e0A8FEeAf206bB36481Bd")
TICKET_ADDRESS  = os.environ.get("TICKET_ADDRESS",   "0xF4b7f91d25Ab667E6535736C168f9B2Ccc944D76")

ABI_DIR = Path(__file__).parent.parent / "abi"

def load_abi(name: str):
    with open(ABI_DIR / f"{name}.json") as f:
        return json.load(f)



def main():
    parser = argparse.ArgumentParser(description="Execute PoHGame.submit()")
    parser.add_argument("--round",  type=int, required=True, help="Round ID (YYYYMMDD)")
    parser.add_argument("--ticket", type=int, required=True, help="ticketTokenId to use")
    parser.add_argument("--answer", type=str, required=True, help="Answer text")
    parser.add_argument("--dry-run", action="store_true", help="Just display contentHash without submitting")
    args = parser.parse_args()

    print(f"📝 Answer: {args.answer}")
    print(f"📏 Answer length: {len(args.answer.encode('utf-8'))} bytes")

    if args.dry_run:
        print("🔍 dry-run mode: Skipping submission")
        return

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print("❌ RPC connection failed:", RPC_URL)
        sys.exit(1)

    account = w3.eth.account.from_key(PRIVATE_KEY)
    my_address = account.address
    print(f"👛 Address: {my_address}")

    ticket = w3.eth.contract(address=Web3.to_checksum_address(TICKET_ADDRESS), abi=load_abi("PoHTicket"))
    game   = w3.eth.contract(address=Web3.to_checksum_address(POHGAME_ADDRESS), abi=load_abi("PoHGame"))

    # Check ticket ownership
    has_ticket = ticket.functions.balanceOf(my_address, args.ticket).call()
    if has_ticket == 0:
        print(f"❌ You do not own ticketTokenId={args.ticket}")
        sys.exit(1)

    # Check remaining uses
    has_uses = ticket.functions.hasUsesRemaining(args.ticket).call()
    if not has_uses:
        print(f"❌ ticketTokenId={args.ticket} has 0 remaining uses (Requires minting a new one)")
        sys.exit(1)

    # Check if round is already finalized
    round_info = game.functions.getRound(args.round).call()
    if round_info[0]:  # finalized
        print(f"❌ roundId={args.round} is already finalized")
        sys.exit(1)

    # Send submit transaction
    print(f"📤 Sending PoHGame.submit()... (roundId={args.round}, ticket={args.ticket})")
    nonce = w3.eth.get_transaction_count(my_address)
    
    # Use EIP-1559 gas price for better compatibility on Base
    priority_fee = w3.to_wei(0.01, 'gwei')
    base_fee = w3.eth.get_block('latest')['baseFeePerGas']
    max_fee = base_fee + priority_fee

    tx = game.functions.submit(
        args.round,
        args.ticket,
        args.answer,
    ).build_transaction({
        "from": my_address,
        "nonce": nonce,
        "gas": 500_000,
        "maxFeePerGas": max_fee,
        "maxPriorityFeePerGas": priority_fee,
        "chainId": w3.eth.chain_id,
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt["status"] == 1:
        print(f"✅ Submission successful! | txHash: {tx_hash.hex()}")
        print(f"   BlockExplorer: https://basescan.org/tx/{tx_hash.hex()}")
    else:
        print(f"❌ Submission failed | txHash: {tx_hash.hex()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
