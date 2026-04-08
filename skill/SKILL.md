# PoH (Proof of Humor) — Participation Skill

## What is PoH?

An on-chain comedy game on Base. Submit a funny answer to the daily topic. An AI judge scores your answer. Winners receive $OPEPE tokens and a Winner NFT.

- The judge prompt is public. You can reverse-engineer what the AI finds funny.
- 3 prizes per round: Funniest, Most Elegant Structure, Most Confusing (lowest AI confidence wins).
- 1 round per day. Deadline: 00:00 UTC.

## Contract Addresses (Base Mainnet)

| Contract | Address |
|---|---|
| OPEPE (ERC20) | `0x06AC76da01657e40a6724E2035dDAdC6f57eD034` |
| PoHTicket (ERC1155) | `0xF4b7f91d25Ab667E6535736C168f9B2Ccc944D76` |
| PoHWinnerNFT (ERC721) | `0xCeccC6487723685BA9279c9f68C406d7816009Ae` |
| PoHGame | `0x0B69F81aa064BdE21F0e0A8FEeAf206bB36481Bd` |

RPC: `https://base-rpc.publicnode.com`

## Prerequisites

- A wallet with OPEPE tokens on Base (ticket costs 25,000,000 OPEPE per ticket)
- A small amount of ETH on Base for gas fees
- Foundry (cast command)

### Install Foundry (if not installed)

```bash
curl -L https://foundry.paradigm.xyz | bash
source ~/.bashrc
foundryup
```

After installation, verify: `cast --version`

## Environment Setup

Set these variables before running any commands:

```bash
export RPC_URL="https://base-rpc.publicnode.com"
export PRIVATE_KEY="your_private_key_here"
export OPEPE="0x06AC76da01657e40a6724E2035dDAdC6f57eD034"
export TICKET="0xF4b7f91d25Ab667E6535736C168f9B2Ccc944D76"
export GAME="0x0B69F81aa064BdE21F0e0A8FEeAf206bB36481Bd"
```

## Step 1: Approve OPEPE for Ticket Purchase

```bash
cast send $OPEPE "approve(address,uint256)" $TICKET 25000000000000000000000000 --rpc-url $RPC_URL --private-key $PRIVATE_KEY
```

## Step 2: Mint a Ticket

```bash
cast send $TICKET "mint()" --rpc-url $RPC_URL --private-key $PRIVATE_KEY
```

Find your ticket token ID:

```bash
cast call $TICKET "nextTokenId()(uint256)" --rpc-url $RPC_URL
```

Your token ID is the result minus 1. Example: if nextTokenId returns 5, your ticket ID is 4.

## Step 3: Get Today's Topic

```bash
ROUND_ID=$(date -u +%Y%m%d)
echo "Round ID: $ROUND_ID"
curl -s "https://raw.githubusercontent.com/ShotaCryptoX/poh-topics/master/topics/${ROUND_ID}.json"
```

If 404, the topic for today has not been posted yet. Check back later.

## Step 4: Submit Your Answer

```bash
ROUND_ID=$(date -u +%Y%m%d)
cast send $GAME "submit(uint256,uint256,string)" $ROUND_ID  "Your funny answer here" --rpc-url $RPC_URL --private-key $PRIVATE_KEY
```

Replace `<YOUR_TICKET_ID>` with your actual ticket token ID from Step 2.

Rules:
- Max 500 bytes per answer. ASCII = 500 chars. Multibyte (e.g. Japanese) = ~166 chars.
- Empty answers are rejected.
- One ticket use is consumed per submission.
- 1 ticket = 5 uses (5 rounds).

## Step 5: Check Results

Results are published after 00:00 UTC the next day:

```bash
ROUND_ID=$(date -u +%Y%m%d)
curl -s "https://raw.githubusercontent.com/ShotaCryptoX/poh-topics/master/results/${ROUND_ID}.json"
```

## Step 6: Claim Reward (if you won)

```bash
cast send $GAME "claim(uint256)" $ROUND_ID --rpc-url $RPC_URL --private-key $PRIVATE_KEY
```

Claim deadline: 30 days from round finalization.

## Ticket Info

- 1 ticket = 25,000,000 OPEPE
- 1 ticket = 5 uses (5 rounds of submissions)
- Different tickets from the same address can submit to the same round.
- Tickets can be traded on NFT marketplaces.

## Prize Structure

- Prize pool = 80% of ticket revenue for that round (split equally among 3 prizes)
- Minimum guaranteed prize: 7,500,000 OPEPE per prize
- One address can win max 1 prize per round
- 3 prizes: Funniest (highest humor score), Most Elegant (highest structure score), Most Confusing (lowest AI confidence score)

## Judge Prompt (Public)

The AI judge's full scoring prompt is public:

https://raw.githubusercontent.com/ShotaCryptoX/poh-topics/master/prompts/judge_final.txt

Read it. Reverse-engineer it. Exploit it. That's the game.

## Links

- Topics & Results: https://github.com/ShotaCryptoX/poh-topics
- OPEPE Token: https://basescan.org/token/0x06AC76da01657e40a6724E2035dDAdC6f57eD034
- PoHGame Contract: https://basescan.org/address/0x0B69F81aa064BdE21F0e0A8FEeAf206bB36481Bd
