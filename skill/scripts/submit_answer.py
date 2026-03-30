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
POHGAME_ADDRESS = os.environ.get("POHGAME_ADDRESS",  "0xB03CfA85f4791778062F221E482107867e7281d5")
TICKET_ADDRESS  = os.environ.get("TICKET_ADDRESS",   "0x8Ad615dA799E4c233028b1643030F802AA857f34")

ABI_DIR = Path(__file__).parent.parent / "abi"

def load_abi(name: str):
    with open(ABI_DIR / f"{name}.json") as f:
        return json.load(f)

from datetime import datetime, timezone, timedelta

def compute_content_hash(answer_text: str) -> bytes:
    """
    contentHash = keccak256(UTF-8 encoded answer text)
    Complies with the specifications outlined in the game rules.
    """
    normalized = answer_text.strip().replace("\r\n", "\n").replace("\r", "\n")
    return keccak(normalized.encode("utf-8"))

def main():
    parser = argparse.ArgumentParser(description="Execute PoHGame.submit()")
    parser.add_argument("--round",  type=int, required=False, help="Round ID (YYYYMMDD) (Default: today in JST)")
    parser.add_argument("--ticket", type=int, required=True, help="ticketTokenId to use")
    parser.add_argument("--answer", type=str, required=True, help="Answer text")
    parser.add_argument("--dry-run", action="store_true", help="Just display contentHash without submitting")
    args = parser.parse_args()

    JST = timezone(timedelta(hours=9))
    round_id = args.round if args.round else int(datetime.now(JST).strftime("%Y%m%d"))

    # Calculate contentHash
    content_hash = compute_content_hash(args.answer)
    content_hash_hex = "0x" + content_hash.hex()
    print(f"📝 Answer: {args.answer}")
    print(f"🔐 contentHash: {content_hash_hex}")
    print(f"📅 Round ID: {round_id}")

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
    round_info = game.functions.getRound(round_id).call()
    if round_info[0]:  # finalized
        print(f"❌ roundId={round_id} is already finalized")
        sys.exit(1)

    # Send submit transaction
    print(f"📤 Sending PoHGame.submit()... (roundId={round_id}, ticket={args.ticket})")
    nonce = w3.eth.get_transaction_count(my_address)
    
    # Use EIP-1559 gas price for better compatibility on Base
    priority_fee = w3.to_wei(0.01, 'gwei')
    base_fee = w3.eth.get_block('latest')['baseFeePerGas']
    max_fee = base_fee + priority_fee

    tx = game.functions.submit(
        round_id,
        args.ticket,
        content_hash,
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
        
        # --- 追加: 回答平文をローカルJSONに保存 ---
        try:
            repo_dir = Path(__file__).parent.parent.parent / "poh-topics"
            submissions_dir = repo_dir / "submissions"
            submissions_dir.mkdir(parents=True, exist_ok=True)
            
            sub_file = submissions_dir / f"{round_id}.json"
            
            if sub_file.exists():
                with open(sub_file, "r", encoding="utf-8") as f:
                    sub_data = json.load(f)
            else:
                sub_data = {
                    "roundId": str(round_id),
                    "submissions": []
                }
            
            # 追記
            sub_data["submissions"].append({
                "address": my_address,
                "ticketId": args.ticket,
                "contentHash": content_hash_hex,
                "answer": args.answer
            })
            
            # 保存
            with open(sub_file, "w", encoding="utf-8") as f:
                json.dump(sub_data, f, ensure_ascii=False, indent=2)
                
            print(f"💾 Saved plaintext answer to {sub_file.name}")
        except Exception as e:
            print(f"⚠️ Failed to save plaintext answer locally: {e}")
            
    else:
        print(f"❌ Submission failed | txHash: {tx_hash.hex()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
