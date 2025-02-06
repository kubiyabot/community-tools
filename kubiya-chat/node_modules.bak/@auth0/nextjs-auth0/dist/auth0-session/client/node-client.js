"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.clientGetter = exports.NodeClient = void 0;
const tslib_1 = require("tslib");
const abstract_client_1 = require("./abstract-client");
const openid_client_1 = require("openid-client");
const errors_1 = require("../utils/errors");
const crypto_1 = require("crypto");
const jose_1 = require("jose");
const url_join_1 = tslib_1.__importDefault(require("url-join"));
const debug_1 = tslib_1.__importDefault(require("../utils/debug"));
const errors_2 = require("../../utils/errors");
const debug = (0, debug_1.default)('client');
function sortSpaceDelimitedString(str) {
    return str.split(' ').sort().join(' ');
}
class NodeClient extends abstract_client_1.AbstractClient {
    async getClient() {
        if (this.client) {
            return this.client;
        }
        const { config, telemetry: { name, version } } = this;
        const defaultHttpOptions = (_url, options) => (Object.assign(Object.assign({}, options), { headers: Object.assign(Object.assign(Object.assign({}, options.headers), { 'User-Agent': `${name}/${version}` }), (config.enableTelemetry
                ? {
                    'Auth0-Client': Buffer.from(JSON.stringify({
                        name,
                        version,
                        env: {
                            node: process.version
                        }
                    })).toString('base64')
                }
                : undefined)), timeout: config.httpTimeout, agent: config.httpAgent }));
        const applyHttpOptionsCustom = (entity) => {
            entity[openid_client_1.custom.http_options] = defaultHttpOptions;
        };
        applyHttpOptionsCustom(openid_client_1.Issuer);
        let issuer;
        try {
            issuer = await openid_client_1.Issuer.discover(config.issuerBaseURL);
        }
        catch (e) {
            throw new errors_1.DiscoveryError(e, config.issuerBaseURL);
        }
        applyHttpOptionsCustom(issuer);
        const issuerTokenAlgs = Array.isArray(issuer.id_token_signing_alg_values_supported)
            ? issuer.id_token_signing_alg_values_supported
            : [];
        if (!issuerTokenAlgs.includes(config.idTokenSigningAlg)) {
            debug('ID token algorithm %o is not supported by the issuer. Supported ID token algorithms are: %o.', config.idTokenSigningAlg, issuerTokenAlgs);
        }
        const configRespType = sortSpaceDelimitedString(config.authorizationParams.response_type);
        const issuerRespTypes = Array.isArray(issuer.response_types_supported) ? issuer.response_types_supported : [];
        issuerRespTypes.map(sortSpaceDelimitedString);
        if (!issuerRespTypes.includes(configRespType)) {
            debug('Response type %o is not supported by the issuer. Supported response types are: %o.', configRespType, issuerRespTypes);
        }
        const configRespMode = config.authorizationParams.response_mode;
        const issuerRespModes = Array.isArray(issuer.response_modes_supported) ? issuer.response_modes_supported : [];
        if (configRespMode && !issuerRespModes.includes(configRespMode)) {
            debug('Response mode %o is not supported by the issuer. Supported response modes are %o.', configRespMode, issuerRespModes);
        }
        if (config.pushedAuthorizationRequests && !issuer.pushed_authorization_request_endpoint) {
            throw new TypeError('pushed_authorization_request_endpoint must be configured on the issuer to use pushedAuthorizationRequests');
        }
        let jwks;
        if (config.clientAssertionSigningKey) {
            const privateKey = (0, crypto_1.createPrivateKey)({ key: config.clientAssertionSigningKey });
            const jwk = await (0, jose_1.exportJWK)(privateKey);
            jwks = { keys: [jwk] };
        }
        this.client = new issuer.Client({
            client_id: config.clientID,
            client_secret: config.clientSecret,
            id_token_signed_response_alg: config.idTokenSigningAlg,
            token_endpoint_auth_method: config.clientAuthMethod,
            token_endpoint_auth_signing_alg: config.clientAssertionSigningAlg
        }, jwks);
        applyHttpOptionsCustom(this.client);
        this.client[openid_client_1.custom.clock_tolerance] = config.clockTolerance;
        const issuerUrl = new URL(issuer.metadata.issuer);
        if (config.idpLogout) {
            if (this.config.idpLogout &&
                (this.config.auth0Logout || (issuerUrl.hostname.match('\\.auth0\\.com$') && this.config.auth0Logout !== false))) {
                Object.defineProperty(this.client, 'endSessionUrl', {
                    value(params) {
                        const { id_token_hint, post_logout_redirect_uri } = params, extraParams = tslib_1.__rest(params, ["id_token_hint", "post_logout_redirect_uri"]);
                        const parsedUrl = new URL((0, url_join_1.default)(issuer.metadata.issuer, '/v2/logout'));
                        parsedUrl.searchParams.set('client_id', config.clientID);
                        post_logout_redirect_uri && parsedUrl.searchParams.set('returnTo', post_logout_redirect_uri);
                        Object.entries(extraParams).forEach(([key, value]) => {
                            if (value === null || value === undefined) {
                                return;
                            }
                            parsedUrl.searchParams.set(key, value);
                        });
                        return parsedUrl.toString();
                    }
                });
            }
            else if (!issuer.end_session_endpoint) {
                debug('the issuer does not support RP-Initiated Logout');
            }
        }
        return this.client;
    }
    async authorizationUrl(parameters) {
        const client = await this.getClient();
        if (this.config.pushedAuthorizationRequests) {
            const { request_uri } = await client.pushedAuthorizationRequest(parameters);
            parameters = { request_uri };
        }
        return client.authorizationUrl(parameters);
    }
    async callbackParams(req) {
        const client = await this.getClient();
        const obj = client.callbackParams({
            method: req.getMethod(),
            url: req.getUrl(),
            body: await req.getBody()
        });
        return new URLSearchParams(obj);
    }
    async callback(redirectUri, parameters, checks, extras) {
        const params = Object.fromEntries(parameters.entries());
        const client = await this.getClient();
        try {
            return await client.callback(redirectUri, params, checks, extras);
        }
        catch (err) {
            if (err instanceof openid_client_1.errors.OPError) {
                throw new errors_1.IdentityProviderError(err);
            }
            else if (err instanceof openid_client_1.errors.RPError) {
                throw new errors_1.ApplicationError(err);
                /* c8 ignore next 3 */
            }
            else {
                throw new errors_1.EscapedError(err.message);
            }
        }
    }
    async endSessionUrl(parameters) {
        const client = await this.getClient();
        return client.endSessionUrl(parameters);
    }
    async userinfo(accessToken) {
        const client = await this.getClient();
        try {
            return await client.userinfo(accessToken);
        }
        catch (e) {
            throw new errors_1.UserInfoError(e.message);
        }
    }
    async refresh(refreshToken, extras) {
        const client = await this.getClient();
        try {
            return await client.refresh(refreshToken, extras);
        }
        catch (e) {
            throw new errors_2.AccessTokenError(errors_2.AccessTokenErrorCode.FAILED_REFRESH_GRANT, 'The request to refresh the access token failed.', new errors_1.IdentityProviderError(e));
        }
    }
    generateRandomCodeVerifier() {
        return openid_client_1.generators.codeVerifier();
    }
    generateRandomNonce() {
        return openid_client_1.generators.nonce();
    }
    calculateCodeChallenge(codeVerifier) {
        return openid_client_1.generators.codeChallenge(codeVerifier);
    }
    async getIssuerMetadata() {
        const { issuer } = await this.getClient();
        return issuer.metadata;
    }
}
exports.NodeClient = NodeClient;
const clientGetter = (telemetry) => {
    let client;
    return async (config) => {
        if (!client) {
            client = new NodeClient(config, telemetry);
        }
        return client;
    };
};
exports.clientGetter = clientGetter;
//# sourceMappingURL=node-client.js.map