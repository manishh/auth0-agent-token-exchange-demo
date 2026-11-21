# Extra experiment: Does the parent token limit what gets issued?

This optional experiment shows why the Action's checks matter. It is not part of the main demo. Read on if you're curious:

**The question:** 

> If the sub-agent asks for a scope that exists on its API but that the parent token never held, does Auth0 still issue it?

## Steps

1. **Add a permission.** In the Search Sub-Agent API, add a permission named `search:admin`.
2. **Give it to the test user.** Add `search:admin` to the test user's role under User Management > Roles.
3. **Authorize the app.** Under Applications > Applications > Parent Agent > API Access, open the Search Sub-Agent API and tick `search:admin`.
4. **Loosen the Action temporarily.** In Authentication > Custom Token Exchange > Sub-agent narrowing > Action Editor, comment out the two `if` blocks that check scopes (the allowlist check and the parent-scope check). Keep every other line, including `const rule`, `requested`, and `parentScopes`. Save and Deploy the Action and wait a few seconds. 
5. **Run the probe** from the repo root (not from inside `extras/`).

   ```bash
   python -m extras.probe search:admin
   ```

## Reading the result

- `granted scope: search:admin` means Auth0 issued a scope the parent token never held. With the checks off, nothing in the Action stopped the request, so the allowlist and the parent-scope check are what protect you.
- A missing `search:admin` means Auth0's own grants stopped the request. The Action still adds an explicit denial and a log entry.

## Clean up

1. Uncomment the two checks in the Action and deploy it again.
2. Run `python run_demo.py` and confirm all 11 checks pass.
3. Remove `search:admin` from the role, from the app's API Access, and from the API's permissions.

---
