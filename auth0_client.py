"""Small helpers for the two Auth0 calls used in the demo."""
from jwt import PyJWKClient
import jwt
import requests

import config

# Fetches and caches the tenant's public signing keys
_jwks_client = PyJWKClient(f"https://{config.AUTH0_DOMAIN}/.well-known/jwks.json")

TIMEOUT_SECONDS = 30
TOKEN_EXCHANGE_GRANT = "urn:ietf:params:oauth:grant-type:token-exchange"


def get_parent_token() -> str:
    """Log in as the test user and return the parent agent's access token.

    The password grant is a demo shortcut that stands in for a real user login.
    """
    response = requests.post(
        config.TOKEN_URL,
        json={
            "grant_type": "password",
            "username": config.TEST_USER,
            "password": config.TEST_PASSWORD,
            "audience": config.PARENT_API,
            "scope": "email:read files:read search:web",
            "client_id": config.CLIENT_ID,
            "client_secret": config.CLIENT_SECRET,
        },
        timeout=TIMEOUT_SECONDS,
    )
    if not response.ok:
        raise RuntimeError(
            f"Could not get the parent token ({response.status_code}): {response.text}"
        )
    return response.json()["access_token"]


def exchange_token(subject_token: str, audience: str, scope: str):
    """Call the token exchange grant. Returns (status_code, response_body)."""
    response = requests.post(
        config.TOKEN_URL,
        json={
            "grant_type": TOKEN_EXCHANGE_GRANT,
            "subject_token": subject_token,
            "subject_token_type": config.SUBJECT_TOKEN_TYPE,
            "audience": audience,
            "scope": scope,
            "client_id": config.CLIENT_ID,
            "client_secret": config.CLIENT_SECRET,
        },
        timeout=TIMEOUT_SECONDS,
    )
    return response.status_code, response.json()


def verify_claims(token: str, audience: str) -> dict:
    """Verify the signature, issuer, audience, and expiry, then return the claims."""
    signing_key = _jwks_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],          # always pin the algorithm
        audience=audience,
        issuer=f"https://{config.AUTH0_DOMAIN}/",   # note the trailing slash
        leeway=10,                     # allow a few seconds of clock skew
    )

#  Only for debugging, not for production use:
def decode_claims(token: str) -> dict:
    """Decode a token's claims for display only.

    Signature verification is switched off for debugging purposes. Never use this
    for authorization decisions.
    """
    return jwt.decode(token, options={"verify_signature": False})