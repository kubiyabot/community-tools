"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.clientGetter = exports.EdgeClient = void 0;
const tslib_1 = require("tslib");
const oauth = tslib_1.__importStar(require("oauth4webapi"));
const jose = tslib_1.__importStar(require("jose"));
const abstract_client_1 = require("./abstract-client");
const errors_1 = require("../utils/errors");
const errors_2 = require("../../utils/errors");
const url_join_1 = tslib_1.__importDefault(require("url-join"));
const encodeBase64 = (input) => {
    const unencoded = new TextEncoder().encode(input);
    const CHUNK_SIZE = 0x8000;
    const arr = [];
    for (let i = 0; i < unencoded.length; i += CHUNK_SIZE) {
        // @ts-expect-error Argument of type 'Uint8Array' is not assignable to parameter of type 'number[]'.
        arr.push(String.fromCharCode.apply(null, unencoded.subarray(i, i + CHUNK_SIZE)));
    }
    return btoa(arr.join(''));
};
class EdgeClient extends abstract_client_1.AbstractClient {
    constructor(config, telemetry) {
        super(config, telemetry);
        this.config = config;
        this.telemetry = telemetry;
        if (config.authorizationParams.response_type !== 'code') {
            throw new Error('This SDK only supports `response_type=code` when used in an Edge runtime.');
        }
        this.httpOptions = () => {
            const headers = new Headers();
            if (config.enableTelemetry) {
                const { name, version } = telemetry;
                headers.set('User-Agent', `${name}/${version}`);
                headers.set('Auth0-Client', encodeBase64(JSON.stringify({
                    name,
                    version,
                    env: {
                        edge: true
                    }
                })));
            }
            return {
                signal: AbortSignal.timeout(this.config.httpTimeout),
                headers
            };
        };
    }
    async getClient() {
        if (this.as) {
            return [this.as, this.client];
        }
        const issuer = new URL(this.config.issuerBaseURL);
        try {
            this.as = await oauth
                .discoveryRequest(issuer, this.httpOptions())
                .then((response) => oauth.processDiscoveryResponse(issuer, response));
        }
        catch (e) {
            throw new errors_1.DiscoveryError(e, this.config.issuerBaseURL);
        }
        if (this.config.pushedAuthorizationRequests && !this.as.pushed_authorization_request_endpoint) {
            throw new TypeError('pushed_authorization_request_endpoint must be configured on the issuer to use pushedAuthorizationRequests');
        }
        this.client = Object.assign(Object.assign({ client_id: this.config.clientID }, (!this.config.clientAssertionSigningKey && { client_secret: this.config.clientSecret })), { token_endpoint_auth_method: this.config.clientAuthMethod, id_token_signed_response_alg: this.config.idTokenSigningAlg, [oauth.clockTolerance]: this.config.clockTolerance });
        return [this.as, this.client];
    }
    async authorizationUrl(parameters) {
        const [as, client] = await this.getClient();
        if (this.config.pushedAuthorizationRequests) {
            const response = await oauth.pushedAuthorizationRequest(as, client, parameters);
            const result = await oauth.processPushedAuthorizationResponse(as, client, response);
            if (oauth.isOAuth2Error(result)) {
                throw new errors_1.IdentityProviderError({
                    message: result.error_description || result.error,
                    error: result.error,
                    error_description: result.error_description
                });
            }
            parameters = { request_uri: result.request_uri };
        }
        const authorizationUrl = new URL(as.authorization_endpoint);
        authorizationUrl.searchParams.set('client_id', this.config.clientID);
        Object.entries(parameters).forEach(([key, value]) => {
            if (value === null || value === undefined) {
                return;
            }
            authorizationUrl.searchParams.set(key, String(value));
        });
        return authorizationUrl.toString();
    }
    async callbackParams(req, expectedState) {
        const [as, client] = await this.getClient();
        const url = req.getMethod().toUpperCase() === 'GET' ? new URL(req.getUrl()) : new URLSearchParams(await req.getBody());
        let result;
        try {
            result = oauth.validateAuthResponse(as, client, url, expectedState);
        }
        catch (e) {
            throw new errors_1.ApplicationError(e);
        }
        if (oauth.isOAuth2Error(result)) {
            throw new errors_1.IdentityProviderError({
                message: result.error_description || result.error,
                error: result.error,
                error_description: result.error_description
            });
        }
        return result;
    }
    async callback(redirectUri, parameters, checks, extras) {
        const [as, client] = await this.getClient();
        const { clientAssertionSigningKey, clientAssertionSigningAlg } = this.config;
        let clientPrivateKey = clientAssertionSigningKey;
        /* c8 ignore next 3 */
        if (clientPrivateKey && !(clientPrivateKey instanceof CryptoKey)) {
            clientPrivateKey = await jose.importPKCS8(clientPrivateKey, clientAssertionSigningAlg || 'RS256');
        }
        const response = await oauth.authorizationCodeGrantRequest(as, client, parameters, redirectUri, checks.code_verifier, Object.assign(Object.assign({ additionalParameters: extras.exchangeBody }, (clientPrivateKey && { clientPrivateKey })), this.httpOptions()));
        const result = await oauth.processAuthorizationCodeOpenIDResponse(as, client, response, checks.nonce, checks.max_age);
        if (oauth.isOAuth2Error(result)) {
            throw new errors_1.IdentityProviderError({
                message: result.error_description || /* c8 ignore next  */ result.error,
                error: result.error,
                error_description: result.error_description
            });
        }
        return result;
    }
    async endSessionUrl(parameters) {
        const [as] = await this.getClient();
        const issuerUrl = new URL(as.issuer);
        if (this.config.idpLogout &&
            (this.config.auth0Logout || (issuerUrl.hostname.match('\\.auth0\\.com$') && this.config.auth0Logout !== false))) {
            const { id_token_hint, post_logout_redirect_uri } = parameters, extraParams = tslib_1.__rest(parameters, ["id_token_hint", "post_logout_redirect_uri"]);
            const auth0LogoutUrl = new URL((0, url_join_1.default)(as.issuer, '/v2/logout'));
            post_logout_redirect_uri && auth0LogoutUrl.searchParams.set('returnTo', post_logout_redirect_uri);
            auth0LogoutUrl.searchParams.set('client_id', this.config.clientID);
            Object.entries(extraParams).forEach(([key, value]) => {
                if (value === null || value === undefined) {
                    return;
                }
                auth0LogoutUrl.searchParams.set(key, value);
            });
            return auth0LogoutUrl.toString();
        }
        if (!as.end_session_endpoint) {
            throw new Error('RP Initiated Logout is not supported on your Authorization Server.');
        }
        const oidcLogoutUrl = new URL(as.end_session_endpoint);
        Object.entries(parameters).forEach(([key, value]) => {
            if (value === null || value === undefined) {
                return;
            }
            oidcLogoutUrl.searchParams.set(key, value);
        });
        oidcLogoutUrl.searchParams.set('client_id', this.config.clientID);
        return oidcLogoutUrl.toString();
    }
    async userinfo(accessToken) {
        const [as, client] = await this.getClient();
        const response = await oauth.userInfoRequest(as, client, accessToken, this.httpOptions());
        try {
            return await oauth.processUserInfoResponse(as, client, oauth.skipSubjectCheck, response);
        }
        catch (e) {
            throw new errors_1.UserInfoError(e.message);
        }
    }
    async refresh(refreshToken, extras) {
        const [as, client] = await this.getClient();
        const res = await oauth.refreshTokenGrantRequest(as, client, refreshToken, Object.assign({ additionalParameters: extras.exchangeBody }, this.httpOptions()));
        const result = await oauth.processRefreshTokenResponse(as, client, res);
        if (oauth.isOAuth2Error(result)) {
            throw new errors_2.AccessTokenError(errors_2.AccessTokenErrorCode.FAILED_REFRESH_GRANT, 'The request to refresh the access token failed.', new errors_1.IdentityProviderError({
                message: result.error_description || /* c8 ignore next  */ result.error,
                error: result.error,
                error_description: result.error_description
            }));
        }
        return result;
    }
    generateRandomCodeVerifier() {
        return oauth.generateRandomCodeVerifier();
    }
    generateRandomNonce() {
        return oauth.generateRandomNonce();
    }
    calculateCodeChallenge(codeVerifier) {
        return oauth.calculatePKCECodeChallenge(codeVerifier);
    }
    async getIssuerMetadata() {
        const [as] = await this.getClient();
        return as;
    }
}
exports.EdgeClient = EdgeClient;
const clientGetter = (telemetry) => {
    let client;
    return async (config) => {
        if (!client) {
            client = new EdgeClient(config, telemetry);
        }
        return client;
    };
};
exports.clientGetter = clientGetter;
//# sourceMappingURL=edge-client.js.map