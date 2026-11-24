"""A finite, integer-weight DTE experiment for the 112-message model.

Weights define an explicit synthetic prior. The encoder samples uniformly
inside the message's proportional interval; the decoder maps uniformly chosen
seeds to messages with approximately the requested probabilities.
"""
from __future__ import annotations
import secrets
from bisect import bisect_right
import honey

# Illustrative model only: weekdays and daytime slots receive larger weights.
DAY_WEIGHTS = {"Monday": 5, "Tuesday": 5, "Wednesday": 5, "Thursday": 5,
               "Friday": 5, "Saturday": 2, "Sunday": 2}
TIME_WEIGHTS = {"9am": 3, "12pm": 5, "3pm": 4, "6pm": 3}
LOCATION_WEIGHTS = {"library": 3, "cafe": 4, "park": 2, "office": 5}


def message_weight(message: str) -> int:
    parts = message.removeprefix("Meet me at ").removesuffix(".").split()
    return LOCATION_WEIGHTS[parts[0]] * DAY_WEIGHTS[parts[2]] * TIME_WEIGHTS[parts[4]]

WEIGHTS = tuple(message_weight(m) for m in honey.MESSAGES)
TOTAL_WEIGHT = sum(WEIGHTS)
BOUNDARIES = tuple((sum(WEIGHTS[:i+1])*honey.SEED_SPACE + TOTAL_WEIGHT-1)//TOTAL_WEIGHT for i in range(honey.MESSAGE_COUNT))
SEED_SPACE = honey.SEED_SPACE


def interval(index: int) -> tuple[int,int]:
    if not 0 <= index < honey.MESSAGE_COUNT:
        raise ValueError("Message index outside supported model")
    lo = 0 if index == 0 else BOUNDARIES[index-1]
    return lo, BOUNDARIES[index]


def encode(message: str) -> bytes:
    try: i=honey.MESSAGES.index(message)
    except ValueError: raise ValueError("Unsupported sentence") from None
    lo,hi=interval(i)
    return (lo+secrets.randbelow(hi-lo)).to_bytes(honey.SEED_BYTES,"big")


def decode(seed: bytes) -> str:
    if len(seed)!=honey.SEED_BYTES: raise ValueError(f"Seed must be {honey.SEED_BYTES} bytes")
    x=int.from_bytes(seed,"big")
    # First cumulative upper boundary strictly greater than x.
    return honey.MESSAGES[bisect_right(BOUNDARIES, x)]


def target_probabilities() -> list[float]:
    return [w/TOTAL_WEIGHT for w in WEIGHTS]
