from hashlib import sha256

MAX_NONCE = 100_000_000_000


def to_sha256(text: str) -> str:
    return sha256(text.encode("ascii")).hexdigest()


def mine(
    block_number: str, transactions: str, previous_hash: str, prefix_zeros: int
) -> str:
    prefix_str = "0" * prefix_zeros

    for nonce in range(MAX_NONCE):
        text = str(block_number) + transactions + previous_hash + str(nonce)
        new_hash = to_sha256(text)

        if new_hash.startswith(prefix_str):
            print(f"Mined bitcoin with nonce: {nonce}")
            return new_hash

    raise Exception(f"Couldn't find correct has after trying {MAX_NONCE} times")
