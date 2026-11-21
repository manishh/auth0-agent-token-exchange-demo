"""Shows how token exchange narrows what a sub-agent inherits.

Run with: python run_demo.py
Every check prints PASS or FAIL. The exit code is 0 only if all checks pass.
"""
import sys

import config
from auth0_client import verify_claims, exchange_token, get_parent_token

results = []


def check(description, passed, detail=""):
    results.append(passed)
    mark = "PASS" if passed else "FAIL"
    suffix = f"  ({detail})" if detail else ""
    print(f"  [{mark}] {description}{suffix}")


def audiences_of(claims):
    aud = claims.get("aud")
    return aud if isinstance(aud, list) else [aud]


def scopes_of(claims):
    return set(claims.get("scope", "").split())


def lifetime_of(claims):
    return claims["exp"] - claims["iat"]


def main():
    # 1. The parent agent's broad token
    print("1. PARENT TOKEN (held by the research agent)")
    try:
        parent_token = get_parent_token()
    except RuntimeError as err:
        check("parent token obtained", False, str(err))
        print("\nRESULT: stopped early. Check the password grant, default directory,")
        print("and the test user's credentials in .env.")
        sys.exit(1)

    parent = verify_claims(parent_token, config.PARENT_API)
    expected_scopes = {"email:read", "files:read", "search:web"}
    check(
        "audience is the Research Agent API",
        config.PARENT_API in audiences_of(parent),
        f"aud={parent.get('aud')}",
    )
    check(
        "holds all three scopes",
        expected_scopes <= scopes_of(parent),
        f"scopes={' '.join(sorted(scopes_of(parent)))}",
    )

    # 2. Exchange it for a search-only token for the sub-agent
    print("\n2. SUB-AGENT TOKEN (after token exchange)")
    status, body = exchange_token(parent_token, config.SEARCH_API, "search:web")
    exchanged = status == 200
    check("exchange succeeded", exchanged, f"HTTP {status}")
    if exchanged:
        sub = verify_claims(body["access_token"], config.SEARCH_API)
        check(
            "audience is the Search Sub-Agent API",
            config.SEARCH_API in audiences_of(sub),
            f"aud={sub.get('aud')}",
        )
        check(
            "scopes are exactly search:web",
            scopes_of(sub) == {"search:web"},
            f"scopes={' '.join(sorted(scopes_of(sub)))}",
        )
        check(
            "lifetime is shorter than the parent's",
            lifetime_of(sub) < lifetime_of(parent),
            f"{lifetime_of(sub)}s vs {lifetime_of(parent)}s",
        )
        check(
            "act claim names the parent agent",
            (sub.get("act") or {}).get("sub") == config.CLIENT_ID,
            f"act={sub.get('act')}",
        )
        check("no refresh token issued", "refresh_token" not in body)
    else:
        print(f"    {body.get('error')}: {body.get('error_description')}")
        print("    Look for a 'fecte' entry in Monitoring > Logs for the cause.")

    # 3. Requests that the Action should refuse
    print("\n3. REQUESTS THAT SHOULD BE DENIED")
    tampered_token = parent_token[:-5] + "XXXXX"
    cases = [
        ("scope escalation (email:read) is denied",
         parent_token, config.SEARCH_API, "email:read", "access_denied"),
        ("wrong audience (Research Agent API) is denied",
         parent_token, config.PARENT_API, "search:web", "access_denied"),
        ("tampered subject token is rejected",
         tampered_token, config.SEARCH_API, "search:web", "invalid_request"),
    ]
    for description, token, audience, scope, expected_error in cases:
        status, body = exchange_token(token, audience, scope)
        check(
            description,
            400 <= status < 500 and body.get("error") == expected_error,
            f"HTTP {status} {body.get('error')}: {body.get('error_description')}",
        )

    # Summary
    passed = sum(results)
    total = len(results)
    print()
    if passed == total:
        print(f"RESULT: ALL {total} CHECKS PASSED")
    else:
        print(f"RESULT: {total - passed} OF {total} CHECKS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()