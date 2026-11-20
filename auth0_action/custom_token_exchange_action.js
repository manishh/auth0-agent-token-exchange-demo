/**
 * =====================================================================
 *  AUTH0 CUSTOM TOKEN EXCHANGE (CTE) ACTION
 * =====================================================================
 *  This file does NOT run locally. Copy it into an Auth0 Action that
 *  uses the "Custom Token Exchange" trigger, then deploy it.
 *
 *  Setup in the Auth0 Dashboard
 *  1. Create the Action with the Custom Token Exchange trigger and
 *     paste this code in.
 *  2. Dependencies tab: add
 *       jsonwebtoken  9.0.2
 *       jwks-rsa      3.1.0
 *  3. Secrets tab: add a secret named PARENT_CLIENT_ID and set it to
 *     the Client ID of your Parent Agent application.
 *  4. Replace the placeholders marked "REPLACE" below.
 *  5. Deploy, then attach the Action to your Token Exchange Profile
 *     (Authentication > Custom Token Exchange).
 *
 *  What it does
 *  - Validates the parent agent's access token (the subject token).
 *  - Checks the request against an allowlist of audience and scopes.
 *  - Records the acting agent in the "act" claim, then approves the
 *    exchange for the same user.
 *  The Action only approves or denies. The issued scopes come from the
 *  request, and the token lifetime comes from the target API settings.
 * =====================================================================
 */

const jwt = require('jsonwebtoken');
const jwksClient = require('jwks-rsa');

// REPLACE: your tenant domain, no https:// and no trailing slash
const DOMAIN = 'YOUR_TENANT.us.auth0.com';

// REPLACE if needed: must match the API identifiers exactly (case and
// trailing slash included). These are the values used in the demo setup.
const PARENT_API = 'https://research-agent.example.com';
const SEARCH_API = 'https://search-agent.example.com';

const jwks = jwksClient({
  jwksUri: `https://${DOMAIN}/.well-known/jwks.json`,
  cache: true,
});

// Checks signature, issuer, audience, and expiry of the parent token
async function validateParentToken(token) {
  try {
    const decoded = jwt.decode(token, { complete: true });
    const key = await jwks.getSigningKey(decoded.header.kid);
    return jwt.verify(token, key.getPublicKey(), {
      algorithms: ['RS256'],
      issuer: `https://${DOMAIN}/`,
      audience: PARENT_API,
    });
  } catch (err) {
    throw new Error('Invalid Token');
  }
}

exports.onExecuteCustomTokenExchange = async (event, api) => {
  // Allowlist: which client may delegate which audience and scopes.
  // The client ID comes from the PARENT_CLIENT_ID secret (Secrets tab).
  const allowlist = {
    [event.secrets.PARENT_CLIENT_ID]: {
      audience: SEARCH_API,
      scopes: ['search:web'],
    },
  };

  // 1. Validate the subject token (the parent's access token)
  let parent;
  try {
    parent = await validateParentToken(event.transaction.subject_token);
  } catch (err) {
    return api.access.rejectInvalidSubjectToken('Invalid subject_token');
  }

  // 2. Check the request against the allowlist
  const rule = allowlist[event.client.client_id];
  const requested = event.transaction.requested_scopes || [];
  const parentScopes = (parent.scope || '').split(' ');

  if (!rule || event.resource_server?.identifier !== rule.audience) {
    return api.access.deny('access_denied', 'Audience not allowed for this client.');
  }
  if (requested.length === 0 || !requested.every((s) => rule.scopes.includes(s))) {
    return api.access.deny('access_denied', 'Requested scopes exceed the allowlist.');
  }
  if (!requested.every((s) => parentScopes.includes(s))) {
    return api.access.deny('access_denied', 'Parent token lacks the requested scopes.');
  }

  // 3. Record the acting agent, then approve the exchange for the same user
  api.authentication.setActor({ sub: event.client.client_id });
  api.authentication.setUserById(parent.sub);
};