"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.fromJson = exports.fromTokenEndpointResponse = void 0;
const tslib_1 = require("tslib");
const jose = tslib_1.__importStar(require("jose"));
/**
 * The user's session.
 *
 * @category Server
 */
class Session {
    constructor(user) {
        this.user = user;
    }
}
exports.default = Session;
/**
 * @ignore
 */
function fromTokenEndpointResponse(tokenEndpointResponse, config) {
    // Get the claims without any OIDC-specific claim.
    const claims = jose.decodeJwt(tokenEndpointResponse.id_token);
    config.identityClaimFilter.forEach((claim) => {
        delete claims[claim];
    });
    const { id_token, access_token, scope, expires_in, expires_at, refresh_token } = tokenEndpointResponse, remainder = tslib_1.__rest(tokenEndpointResponse, ["id_token", "access_token", "scope", "expires_in", "expires_at", "refresh_token"]);
    const storeIDToken = config.session.storeIDToken;
    return Object.assign(new Session(Object.assign({}, claims)), Object.assign({ accessToken: access_token, accessTokenScope: scope, accessTokenExpiresAt: Math.floor(Date.now() / 1000) + Number(expires_in), refreshToken: refresh_token }, (storeIDToken && { idToken: id_token })), remainder);
}
exports.fromTokenEndpointResponse = fromTokenEndpointResponse;
/**
 * @ignore
 */
function fromJson(json) {
    if (!json) {
        return null;
    }
    return Object.assign(new Session(Object.assign({}, json.user)), json);
}
exports.fromJson = fromJson;
//# sourceMappingURL=session.js.map