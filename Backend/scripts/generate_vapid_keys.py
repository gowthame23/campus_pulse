"""
Generate VAPID Key Pair for Web Push Notifications.
Usage:
    python scripts/generate_vapid_keys.py
"""
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat


def generate_vapid_keys():
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    raw_pub = public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
    raw_priv = private_key.private_numbers().private_value.to_bytes(32, "big")

    public_key_b64 = base64.urlsafe_b64encode(raw_pub).rstrip(b"=").decode("utf-8")
    private_key_b64 = base64.urlsafe_b64encode(raw_priv).rstrip(b"=").decode("utf-8")

    print("\n--- Generated VAPID Keys ---")
    print(f"VAPID_PUBLIC_KEY={public_key_b64}")
    print(f"VAPID_PRIVATE_KEY={private_key_b64}")
    print("VAPID_SUBJECT=mailto:admin@campuspulse.edu")
    print("----------------------------\n")
    print("Add these variables to your Backend/.env file to enable Web Push notifications.")


if __name__ == "__main__":
    generate_vapid_keys()
