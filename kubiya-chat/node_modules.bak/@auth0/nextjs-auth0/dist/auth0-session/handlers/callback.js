"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const tslib_1 = require("tslib");
const url_join_1 = tslib_1.__importDefault(require("url-join"));
const encoding_1 = require("../utils/encoding");
const errors_1 = require("../utils/errors");
function getRedirectUri(config) {
    return (0, url_join_1.default)(config.baseURL, config.routes.callback);
}
function callbackHandlerFactory(getConfig, getClient, sessionCache, transientCookieHandler) {
    const getConfigFn = typeof getConfig === 'function' ? getConfig : () => getConfig;
    return async (req, res, options) => {
        const config = await getConfigFn(req);
        const client = await getClient(config);
        const redirectUri = (options === null || options === void 0 ? void 0 : options.redirectUri) || getRedirectUri(config);
        let tokenResponse;
        let authVerification;
        const cookie = await transientCookieHandler.read(config.transactionCookie.name, req, res);
        if (!cookie) {
            throw new errors_1.MissingStateCookieError();
        }
        try {
            authVerification = JSON.parse(cookie);
        }
        catch (_) {
            throw new errors_1.MalformedStateCookieError();
        }
        const { max_age, code_verifier, nonce, state: expectedState, response_type = config.authorizationParams.response_type } = authVerification;
        let callbackParams;
        try {
            callbackParams = await client.callbackParams(req, expectedState);
        }
        catch (err) {
            err.status = 400;
            err.statusCode = 400;
            err.openIdState = (0, encoding_1.decodeState)(expectedState);
            throw err;
        }
        if (!callbackParams.get('state')) {
            throw new errors_1.MissingStateParamError();
        }
        try {
            tokenResponse = await client.callback(redirectUri, callbackParams, {
                max_age: max_age !== undefined ? +max_age : undefined,
                code_verifier,
                nonce,
                state: expectedState,
                response_type
            }, { exchangeBody: options === null || options === void 0 ? void 0 : options.authorizationParams });
        }
        catch (err) {
            err.status = 400;
            err.statusCode = 400;
            err.openIdState = (0, encoding_1.decodeState)(expectedState);
            throw err;
        }
        const openidState = (0, encoding_1.decodeState)(expectedState);
        let session = await sessionCache.fromTokenEndpointResponse(req, res, tokenResponse);
        if (options === null || options === void 0 ? void 0 : options.afterCallback) {
            session = await options.afterCallback(session, openidState);
        }
        if (session) {
            await sessionCache.create(req.req, res.res, session);
        }
        res.redirect(openidState.returnTo || config.baseURL);
    };
}
exports.default = callbackHandlerFactory;
//# sourceMappingURL=callback.js.map