from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, InvalidHashError, VerificationError, VerifyMismatchError

hasher = PasswordHasher()


def hash_password(plain_password):
    return hasher.hash(plain_password)


def verify_password(plain_password, hashed_password):
    try:
        return hasher.verify(hashed_password, plain_password)
    except (
        VerifyMismatchError,
        VerificationError,
        InvalidHashError,
        InvalidHash,
        TypeError,
        ValueError,
    ):
        return False


if __name__ == "__main__":
    stored = hash_password("correct-horse")
    print(f"the stored hash begins: {stored[:48]}... and then a salt that differs every time")
    print(f"the right password verifies : {verify_password('correct-horse', stored)}")
    print(f"a different one does not    : {verify_password('wrong-password', stored)}")
