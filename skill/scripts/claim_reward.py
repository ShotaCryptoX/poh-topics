#!/usr/bin/env python3
"""
claim_reward.py — Claim in-game rewards via PoHGame.claim()

Usage:
    python claim_reward.py --round 20260304
    python claim_reward.py --round 20260304 --dry-run

Environment variables (set in .env file):
    PRIVATE_KEY       : Private key (with or without 0x)
    RPC_URL           : Base Mainnet RPC endpoint
    POHGAME_ADDRESS   : PoHGame Contract Address
"""

import os
import json
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3
from datetime import datetime

# Load .env
load_dotenv(Path(__file__).parent.parent / ".env")

PRIVATE_KEY     = os.environ["PRIVATE_KEY"]
RPC_URL         = os.environ.get("RPC_URL",         "https://mainnet.base.org")
POHGAME_ADDRESS = os.environ.get("POHGAME_ADDRESS", "0xB03CfA85f4791778062F221E482107867e7281d5")

ABI_DIR = Path(__file__).parent.parent / "abi"

def load_abi(name: str):
    with open(ABI_DIR / f"{name}.json") as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="Execute PoHGame.claim()")
    parser.add_argument("--round", type=int, required=True, help="Round ID (YYYYMMDD)")
    parser.add_argument("--dry-run", action="store_true", help="Just display status without submitting")
    args = parser.parse_args()

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print("❌ RPC connection failed:", RPC_URL)
        sys.exit(1)

    account = w3.eth.account.from_key(PRIVATE_KEY)
    my_address = account.address
    print(f"👛 Address: {my_address}")

    game = w3.eth.contract(address=Web3.to_checksum_address(POHGAME_ADDRESS), abi=load_abi("PoHGame"))

    # Check if the round is finalized
    round_info = game.functions.getRound(args.round).call()
    is_finalized = round_info[0]
    if not is_finalized:
        print(f"⏳ roundId={args.round} is still waiting to be finalized. Please retry later.")
        sys.exit(0)

    # Check for victory
    is_winner = game.functions.isWinner(args.round, my_address).call()
    if not is_winner:
        print(f"😢 You did not win an award in roundId={args.round}")
        sys.exit(0)

    # Check deadline
    deadline = game.functions.claimDeadline(args.round, my_address).call()
    deadline_dt = datetime.fromtimestamp(deadline)
    now_ts = int(datetime.now().timestamp())
    print(f"🏆 Award confirmed! claimDeadline: {deadline_dt.strftime('%Y-%m-%d %H:%M:%S')}")

    if now_ts > deadline:
        print("❌ Claim period has expired (past 30 days)")
        sys.exit(1)

    # Check if already claimed
    already = game.functions.claimed(args.round, my_address).call()
    if already:
        print("ℹ️  Game rewards have already been claimed")
        sys.exit(0)

    # Expected in-game tokens
    prize = round_info[7]  # prizePerWinner
    print(f"💰 Expected game tokens: {prize} OPEPE wei")

    if args.dry_run:
        print("🔍 dry-run mode: Skipping submission")
        return

    # Send claim transaction
    print("📤 Sending PoHGame.claim()...")
    nonce = w3.eth.get_transaction_count(my_address)
    
    # Use EIP-1559 gas price for better compatibility on Base
    priority_fee = w3.to_wei(0.01, 'gwei')
    base_fee = w3.eth.get_block('latest')['baseFeePerGas']
    max_fee = base_fee + priority_fee

    tx = game.functions.claim(args.round).build_transaction({
        "from": my_address,
        "nonce": nonce,
        "gas": 150_000,
        "maxFeePerGas": max_fee,
        "maxPriorityFeePerGas": priority_fee,
        "chainId": w3.eth.chain_id,
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt["status"] == 1:
        print(f"✅ Claim successful! | txHash: {tx_hash.hex()}")
        print(f"   BlockExplorer: https://basescan.org/tx/{tx_hash.hex()}")
    else:
        print(f"❌ Claim failed | txHash: {tx_hash.hex()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
