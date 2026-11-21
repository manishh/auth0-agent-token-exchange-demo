"""Probe: request a scope for the search audience and show what Auth0 grants.

Run from the repo root:  python -m extras.probe [scope]
Default scope: email:read
"""
import json
import sys

import config
from auth0_client import verify_claims, exchange_token, get_parent_token

scope = sys.argv[1] if len(sys.argv) > 1 else "email:read"
parent = get_parent_token()
status, body = exchange_token(parent, config.SEARCH_API, scope)
print("HTTP", status)
if status == 200:
    claims = verify_claims(body["access_token"], config.SEARCH_API)
    print("requested scope :", scope)
    print("granted scope   :", claims.get("scope", "(none)"))
    print("permissions     :", claims.get("permissions"))
    print(json.dumps(claims, indent=2))
else:
    print(json.dumps(body, indent=2))