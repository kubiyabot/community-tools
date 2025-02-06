"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const tslib_1 = require("tslib");
const url_join_1 = tslib_1.__importDefault(require("url-join"));
const encoding_1 = require("../utils/encoding");
const debug_1 = tslib_1.__importDefault(require("../utils/debug"));
const debug = (0, debug_1.default)('handlers');
function getRedirectUri(config) {
    return (0, url_join_1.default)(config.baseURL, config.routes.callback);
}
function loginHandlerFactory(getConfig, getClient, transientHandler) {
    const getConfigFn = typeof getConfig === 'function' ? getConfig : () => getConfig;
    return async (req, res, options = {}) => {
        const config = await getConfigFn(req);
        const client = await getClient(config);
        const returnTo = options.returnTo || config.baseURL;
        const opts = Object.assign({ returnTo, getLoginState: config.getLoginState }, options);
        // Ensure a redirect_uri, merge in configuration options, then passed-in options.
        opts.authorizationParams = Object.assign(Object.assign({ redirect_uri: getRedirectUri(config) }, config.authorizationParams), (opts.authorizationParams || {}));
        const stateValue = await opts.getLoginState(opts);
        if (typeof stateValue !== 'object') {
            throw new Error('Custom state value must be an object.');
        }
        stateValue.nonce = client.generateRandomNonce();
        stateValue.returnTo = stateValue.returnTo || opts.returnTo;
        const responseType = opts.authorizationParams.response_type;
        const usePKCE = responseType.includes('code');
        if (usePKCE) {
            debug('response_type includes code, the authorization request will use PKCE');
            stateValue.code_verifier = client.generateRandomCodeVerifier();
        }
        const validResponseTypes = ['id_token', 'code id_token', 'code'];
        if (!validResponseTypes.includes(responseType)) {
            throw new Error(`response_type should be one of ${validResponseTypes.join(', ')}`);
        }
        if (!/\bopenid\b/.test(opts.authorizationParams.scope)) {
            throw new Error('scope should contain "openid"');
        }
        const authVerification = {
            nonce: client.generateRandomNonce(),
            state: (0, encoding_1.encodeState)(stateValue)
        };
        if (opts.authorizationParams.max_age) {
            authVerification.max_age = opts.authorizationParams.max_age;
        }
        const authParams = Object.assign(Object.assign({}, opts.authorizationParams), authVerification);
        if (usePKCE) {
            authVerification.code_verifier = client.generateRandomCodeVerifier();
            authParams.code_challenge_method = 'S256';
            authParams.code_challenge = await client.calculateCodeChallenge(authVerification.code_verifier);
        }
        if (responseType !== config.authorizationParams.response_type) {
            authVerification.response_type = responseType;
        }
        await transientHandler.save(config.transactionCookie.name, req, res, {
            sameSite: authParams.response_mode === 'form_post' ? 'none' : config.transactionCookie.sameSite,
            value: JSON.stringify(authVerification)
        });
        const authorizationUrl = await client.authorizationUrl(authParams);
        debug('redirecting to %s', authorizationUrl);
        res.redirect(authorizationUrl);
    };
}
exports.default = loginHandlerFactory;
//# sourceMappingURL=login.js.map