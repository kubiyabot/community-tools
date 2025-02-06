"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const errors_1 = require("../utils/errors");
const array_1 = require("../utils/array");
const session_1 = require("../session");
const cache_1 = require("./cache");
const http_1 = require("../http");
/**
 * @ignore
 */
function accessTokenFactory(getConfig, getClient, sessionCache) {
    return async (reqOrOpts, res, accessTokenRequest) => {
        const options = (res ? accessTokenRequest : reqOrOpts);
        const req = (res ? reqOrOpts : undefined);
        const config = await getConfig(req ? (0, cache_1.getAuth0ReqRes)(req, res)[0] : new http_1.Auth0NextRequestCookies());
        const client = await getClient(config);
        const parts = await (0, session_1.get)({ sessionCache, req, res });
        let [session] = parts;
        const [, iat] = parts;
        if (!session) {
            throw new errors_1.AccessTokenError(errors_1.AccessTokenErrorCode.MISSING_SESSION, 'The user does not have a valid session.');
        }
        if (!session.accessToken && !session.refreshToken) {
            throw new errors_1.AccessTokenError(errors_1.AccessTokenErrorCode.MISSING_ACCESS_TOKEN, 'The user does not have a valid access token.');
        }
        if (!session.accessTokenExpiresAt) {
            throw new errors_1.AccessTokenError(errors_1.AccessTokenErrorCode.EXPIRED_ACCESS_TOKEN, 'Expiration information for the access token is not available. The user will need to sign in again.');
        }
        if (options && options.scopes) {
            const persistedScopes = session.accessTokenScope;
            if (!persistedScopes || persistedScopes.length === 0) {
                throw new errors_1.AccessTokenError(errors_1.AccessTokenErrorCode.INSUFFICIENT_SCOPE, 'An access token with the requested scopes could not be provided. The user will need to sign in again.');
            }
            const matchingScopes = (0, array_1.intersect)(options.scopes, persistedScopes.split(' '));
            if (!(0, array_1.match)(options.scopes, [...matchingScopes])) {
                throw new errors_1.AccessTokenError(errors_1.AccessTokenErrorCode.INSUFFICIENT_SCOPE, `Could not retrieve an access token with scopes "${options.scopes.join(' ')}". The user will need to sign in again.`);
            }
        }
        // Check if the token has expired.
        // There is an edge case where we might have some clock skew where our code assumes the token is still valid.
        // Adding a skew of 1 minute to compensate.
        if (!session.refreshToken && session.accessTokenExpiresAt * 1000 - 60000 < Date.now()) {
            throw new errors_1.AccessTokenError(errors_1.AccessTokenErrorCode.EXPIRED_ACCESS_TOKEN, 'The access token expired and a refresh token is not available. The user will need to sign in again.');
        }
        if ((options === null || options === void 0 ? void 0 : options.refresh) && !session.refreshToken) {
            throw new errors_1.AccessTokenError(errors_1.AccessTokenErrorCode.MISSING_REFRESH_TOKEN, 'A refresh token is required to refresh the access token, but none is present.');
        }
        // Check if the token has expired.
        // There is an edge case where we might have some clock skew where our code assumes the token is still valid.
        // Adding a skew of 1 minute to compensate.
        if ((session.refreshToken && session.accessTokenExpiresAt * 1000 - 60000 < Date.now()) ||
            (session.refreshToken && options && options.refresh)) {
            const tokenSet = await client.refresh(session.refreshToken, {
                exchangeBody: options === null || options === void 0 ? void 0 : options.authorizationParams
            });
            // Update the session.
            const newSession = (0, session_1.fromTokenEndpointResponse)(tokenSet, config);
            Object.assign(session, Object.assign(Object.assign({}, newSession), { refreshToken: newSession.refreshToken || session.refreshToken, user: Object.assign(Object.assign({}, session.user), newSession.user) }));
            if (options === null || options === void 0 ? void 0 : options.afterRefresh) {
                if (req) {
                    session = await options.afterRefresh(req, res, session);
                }
                else {
                    session = await options.afterRefresh(session);
                }
            }
            await (0, session_1.set)({ sessionCache, req, res, session, iat });
            // Return the new access token.
            return {
                accessToken: tokenSet.access_token
            };
        }
        // We don't have an access token.
        if (!session.accessToken) {
            throw new errors_1.AccessTokenError(errors_1.AccessTokenErrorCode.MISSING_ACCESS_TOKEN, 'The user does not have a valid access token.');
        }
        // The access token is not expired and has sufficient scopes.
        return {
            accessToken: session.accessToken
        };
    };
}
exports.default = accessTokenFactory;
//# sourceMappingURL=get-access-token.js.map