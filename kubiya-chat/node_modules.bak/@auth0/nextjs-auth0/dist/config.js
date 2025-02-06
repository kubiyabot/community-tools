"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.configSingletonGetter = exports.getConfig = void 0;
const tslib_1 = require("tslib");
const get_config_1 = require("./auth0-session/get-config");
/**
 * @ignore
 */
const FALSEY = ['n', 'no', 'false', '0', 'off'];
/**
 * @ignore
 */
const bool = (param, defaultValue) => {
    if (param === undefined || param === '')
        return defaultValue;
    if (param && typeof param === 'string')
        return !FALSEY.includes(param.toLowerCase().trim());
    return !!param;
};
/**
 * @ignore
 */
const num = (param) => (param === undefined || param === '' ? undefined : +param);
/**
 * @ignore
 */
const array = (param) => param === undefined || param === '' ? undefined : param.replace(/\s/g, '').split(',');
/**
 * @ignore
 */
const getConfig = (params = {}) => {
    var _a, _b, _c, _d;
    // Don't use destructuring here so that the `DefinePlugin` can replace any env vars specified in `next.config.js`
    const AUTH0_SECRET = process.env.AUTH0_SECRET;
    const AUTH0_ISSUER_BASE_URL = process.env.AUTH0_ISSUER_BASE_URL;
    const AUTH0_BASE_URL = process.env.AUTH0_BASE_URL || process.env.NEXT_PUBLIC_AUTH0_BASE_URL;
    const AUTH0_CLIENT_ID = process.env.AUTH0_CLIENT_ID;
    const AUTH0_CLIENT_SECRET = process.env.AUTH0_CLIENT_SECRET;
    const AUTH0_CLOCK_TOLERANCE = process.env.AUTH0_CLOCK_TOLERANCE;
    const AUTH0_HTTP_TIMEOUT = process.env.AUTH0_HTTP_TIMEOUT;
    const AUTH0_ENABLE_TELEMETRY = process.env.AUTH0_ENABLE_TELEMETRY;
    const AUTH0_IDP_LOGOUT = process.env.AUTH0_IDP_LOGOUT;
    const AUTH0_LOGOUT = process.env.AUTH0_LOGOUT;
    const AUTH0_ID_TOKEN_SIGNING_ALG = process.env.AUTH0_ID_TOKEN_SIGNING_ALG;
    const AUTH0_LEGACY_SAME_SITE_COOKIE = process.env.AUTH0_LEGACY_SAME_SITE_COOKIE;
    const AUTH0_IDENTITY_CLAIM_FILTER = process.env.AUTH0_IDENTITY_CLAIM_FILTER;
    const AUTH0_PUSHED_AUTHORIZATION_REQUESTS = process.env.AUTH0_PUSHED_AUTHORIZATION_REQUESTS;
    const AUTH0_CALLBACK = process.env.AUTH0_CALLBACK;
    const AUTH0_POST_LOGOUT_REDIRECT = process.env.AUTH0_POST_LOGOUT_REDIRECT;
    const AUTH0_AUDIENCE = process.env.AUTH0_AUDIENCE;
    const AUTH0_SCOPE = process.env.AUTH0_SCOPE;
    const AUTH0_ORGANIZATION = process.env.AUTH0_ORGANIZATION;
    const AUTH0_SESSION_NAME = process.env.AUTH0_SESSION_NAME;
    const AUTH0_SESSION_ROLLING = process.env.AUTH0_SESSION_ROLLING;
    const AUTH0_SESSION_ROLLING_DURATION = process.env.AUTH0_SESSION_ROLLING_DURATION;
    const AUTH0_SESSION_ABSOLUTE_DURATION = process.env.AUTH0_SESSION_ABSOLUTE_DURATION;
    const AUTH0_SESSION_AUTO_SAVE = process.env.AUTH0_SESSION_AUTO_SAVE;
    const AUTH0_SESSION_STORE_ID_TOKEN = process.env.AUTH0_SESSION_STORE_ID_TOKEN;
    const AUTH0_COOKIE_DOMAIN = process.env.AUTH0_COOKIE_DOMAIN;
    const AUTH0_COOKIE_PATH = process.env.AUTH0_COOKIE_PATH;
    const AUTH0_COOKIE_TRANSIENT = process.env.AUTH0_COOKIE_TRANSIENT;
    const AUTH0_COOKIE_HTTP_ONLY = process.env.AUTH0_COOKIE_HTTP_ONLY;
    const AUTH0_COOKIE_SECURE = process.env.AUTH0_COOKIE_SECURE;
    const AUTH0_COOKIE_SAME_SITE = process.env.AUTH0_COOKIE_SAME_SITE;
    const AUTH0_CLIENT_ASSERTION_SIGNING_KEY = process.env.AUTH0_CLIENT_ASSERTION_SIGNING_KEY;
    const AUTH0_CLIENT_ASSERTION_SIGNING_ALG = process.env.AUTH0_CLIENT_ASSERTION_SIGNING_ALG;
    const AUTH0_TRANSACTION_COOKIE_NAME = process.env.AUTH0_TRANSACTION_COOKIE_NAME;
    const AUTH0_TRANSACTION_COOKIE_DOMAIN = process.env.AUTH0_TRANSACTION_COOKIE_DOMAIN;
    const AUTH0_TRANSACTION_COOKIE_PATH = process.env.AUTH0_TRANSACTION_COOKIE_PATH;
    const AUTH0_TRANSACTION_COOKIE_SAME_SITE = process.env.AUTH0_TRANSACTION_COOKIE_SAME_SITE;
    const AUTH0_TRANSACTION_COOKIE_SECURE = process.env.AUTH0_TRANSACTION_COOKIE_SECURE;
    const baseURL = AUTH0_BASE_URL && !/^https?:\/\//.test(AUTH0_BASE_URL) ? `https://${AUTH0_BASE_URL}` : AUTH0_BASE_URL;
    const { organization } = params, baseParams = tslib_1.__rest(params, ["organization"]);
    const baseConfig = (0, get_config_1.get)(Object.assign(Object.assign({ secret: AUTH0_SECRET, issuerBaseURL: AUTH0_ISSUER_BASE_URL, baseURL: baseURL, clientID: AUTH0_CLIENT_ID, clientSecret: AUTH0_CLIENT_SECRET, clockTolerance: num(AUTH0_CLOCK_TOLERANCE), httpTimeout: num(AUTH0_HTTP_TIMEOUT), enableTelemetry: bool(AUTH0_ENABLE_TELEMETRY), idpLogout: bool(AUTH0_IDP_LOGOUT, true), auth0Logout: bool(AUTH0_LOGOUT, true), idTokenSigningAlg: AUTH0_ID_TOKEN_SIGNING_ALG, legacySameSiteCookie: bool(AUTH0_LEGACY_SAME_SITE_COOKIE), identityClaimFilter: array(AUTH0_IDENTITY_CLAIM_FILTER), pushedAuthorizationRequests: bool(AUTH0_PUSHED_AUTHORIZATION_REQUESTS, false) }, baseParams), { authorizationParams: Object.assign({ response_type: 'code', audience: AUTH0_AUDIENCE, scope: AUTH0_SCOPE }, baseParams.authorizationParams), session: Object.assign(Object.assign({ name: AUTH0_SESSION_NAME, rolling: bool(AUTH0_SESSION_ROLLING), rollingDuration: AUTH0_SESSION_ROLLING_DURATION && isNaN(Number(AUTH0_SESSION_ROLLING_DURATION))
                ? bool(AUTH0_SESSION_ROLLING_DURATION)
                : num(AUTH0_SESSION_ROLLING_DURATION), absoluteDuration: AUTH0_SESSION_ABSOLUTE_DURATION && isNaN(Number(AUTH0_SESSION_ABSOLUTE_DURATION))
                ? bool(AUTH0_SESSION_ABSOLUTE_DURATION)
                : num(AUTH0_SESSION_ABSOLUTE_DURATION), autoSave: bool(AUTH0_SESSION_AUTO_SAVE, true), storeIDToken: bool(AUTH0_SESSION_STORE_ID_TOKEN) }, baseParams.session), { cookie: Object.assign({ domain: AUTH0_COOKIE_DOMAIN, path: AUTH0_COOKIE_PATH || '/', transient: bool(AUTH0_COOKIE_TRANSIENT), httpOnly: bool(AUTH0_COOKIE_HTTP_ONLY), secure: bool(AUTH0_COOKIE_SECURE), sameSite: AUTH0_COOKIE_SAME_SITE }, (_a = baseParams.session) === null || _a === void 0 ? void 0 : _a.cookie) }), routes: {
            callback: ((_b = baseParams.routes) === null || _b === void 0 ? void 0 : _b.callback) || AUTH0_CALLBACK || '/api/auth/callback',
            postLogoutRedirect: ((_c = baseParams.routes) === null || _c === void 0 ? void 0 : _c.postLogoutRedirect) || AUTH0_POST_LOGOUT_REDIRECT
        }, clientAssertionSigningKey: AUTH0_CLIENT_ASSERTION_SIGNING_KEY, clientAssertionSigningAlg: AUTH0_CLIENT_ASSERTION_SIGNING_ALG, transactionCookie: Object.assign({ name: AUTH0_TRANSACTION_COOKIE_NAME, domain: AUTH0_TRANSACTION_COOKIE_DOMAIN, path: AUTH0_TRANSACTION_COOKIE_PATH || '/', secure: bool(AUTH0_TRANSACTION_COOKIE_SECURE), sameSite: AUTH0_TRANSACTION_COOKIE_SAME_SITE }, baseParams.transactionCookie) }));
    return Object.assign(Object.assign({}, baseConfig), { organization: organization || AUTH0_ORGANIZATION, routes: Object.assign(Object.assign({}, baseConfig.routes), { login: ((_d = baseParams.routes) === null || _d === void 0 ? void 0 : _d.login) || process.env.NEXT_PUBLIC_AUTH0_LOGIN || '/api/auth/login' }) });
};
exports.getConfig = getConfig;
const configSingletonGetter = (params = {}, genId) => {
    let config;
    return (req) => {
        if (!config) {
            // Bails out of static rendering for Server Components
            // Need to query cookies because Server Components don't have access to URL
            req.getCookies();
            if ('getUrl' in req) {
                // Bail out of static rendering for API Routes
                // Reading cookies is not always enough https://github.com/vercel/next.js/issues/49006
                req.getUrl();
            }
            config = (0, exports.getConfig)(Object.assign(Object.assign({}, params), { session: Object.assign({ genId }, params.session) }));
        }
        return config;
    };
};
exports.configSingletonGetter = configSingletonGetter;
//# sourceMappingURL=config.js.map