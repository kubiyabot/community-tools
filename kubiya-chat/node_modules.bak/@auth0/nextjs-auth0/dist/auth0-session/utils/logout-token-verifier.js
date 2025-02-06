"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const jose_1 = require("jose");
function getLogoutTokenVerifier() {
    let remoteJwkSet;
    return async (logoutToken, config, issuerMetadata) => {
        let keyInput;
        if (config.idTokenSigningAlg === 'RS256') {
            if (!remoteJwkSet) {
                remoteJwkSet = (0, jose_1.createRemoteJWKSet)(new URL(issuerMetadata.jwks_uri));
            }
            keyInput = remoteJwkSet;
        }
        else {
            keyInput = new TextEncoder().encode(config.clientSecret);
        }
        const { payload } = await (0, jose_1.jwtVerify)(logoutToken, keyInput, {
            issuer: issuerMetadata.issuer,
            audience: config.clientID,
            algorithms: [config.idTokenSigningAlg],
            requiredClaims: ['iat']
        });
        if (!('sid' in payload) && !('sub' in payload)) {
            throw new Error('either "sid" or "sub" (or both) claims must be present');
        }
        if ('nonce' in payload) {
            throw new Error('"nonce" claim is prohibited');
        }
        if (!('events' in payload)) {
            throw new Error('"events" claim is missing');
        }
        if (typeof payload.events !== 'object' || payload.events === null) {
            throw new Error('"events" claim must be an object');
        }
        if (!('http://schemas.openid.net/event/backchannel-logout' in payload.events)) {
            throw new Error('"http://schemas.openid.net/event/backchannel-logout" member is missing in the "events" claim');
        }
        if (typeof payload.events['http://schemas.openid.net/event/backchannel-logout'] !== 'object') {
            throw new Error('"http://schemas.openid.net/event/backchannel-logout" member in the "events" claim must be an object');
        }
        return payload;
    };
}
exports.default = getLogoutTokenVerifier;
//# sourceMappingURL=logout-token-verifier.js.map