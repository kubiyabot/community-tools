"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports._initAuth = void 0;
const tslib_1 = require("tslib");
const auth0_session_1 = require("./auth0-session");
const handlers_1 = require("./handlers");
const session_1 = require("./session/");
const helpers_1 = require("./helpers");
const config_1 = require("./config");
const shared_1 = require("./shared");
const with_middleware_auth_required_1 = tslib_1.__importDefault(require("./helpers/with-middleware-auth-required"));
const _initAuth = ({ params, genId, clientGetter }) => {
    const getConfig = (0, config_1.configSingletonGetter)(params, genId);
    const getClient = clientGetter(shared_1.telemetry);
    // Init base layer (with base config)
    const transientStore = new auth0_session_1.TransientStore(getConfig);
    const sessionCache = new session_1.SessionCache(getConfig);
    const baseHandleLogin = (0, auth0_session_1.loginHandler)(getConfig, getClient, transientStore);
    const baseHandleLogout = (0, auth0_session_1.logoutHandler)(getConfig, getClient, sessionCache);
    const baseHandleCallback = (0, auth0_session_1.callbackHandler)(getConfig, getClient, sessionCache, transientStore);
    const baseHandleBackchannelLogout = (0, auth0_session_1.backchannelLogoutHandler)(getConfig, getClient);
    // Init Next layer (with next config)
    const getSession = (0, session_1.sessionFactory)(sessionCache);
    const touchSession = (0, session_1.touchSessionFactory)(sessionCache);
    const updateSession = (0, session_1.updateSessionFactory)(sessionCache);
    const getAccessToken = (0, session_1.accessTokenFactory)(getConfig, getClient, sessionCache);
    const withApiAuthRequired = (0, helpers_1.withApiAuthRequiredFactory)(sessionCache);
    const withPageAuthRequired = (0, helpers_1.withPageAuthRequiredFactory)(getConfig, sessionCache);
    const handleLogin = (0, handlers_1.loginHandler)(baseHandleLogin, getConfig);
    const handleLogout = (0, handlers_1.logoutHandler)(baseHandleLogout);
    const handleCallback = (0, handlers_1.callbackHandler)(baseHandleCallback, getConfig);
    const handleBackchannelLogout = (0, handlers_1.backchannelLogoutHandler)(baseHandleBackchannelLogout, getConfig);
    const handleProfile = (0, handlers_1.profileHandler)(getConfig, getClient, getAccessToken, sessionCache);
    const handleAuth = (0, handlers_1.handlerFactory)({
        handleLogin,
        handleLogout,
        handleCallback,
        handleProfile,
        handleBackchannelLogout
    });
    const withMiddlewareAuthRequired = (0, with_middleware_auth_required_1.default)(getConfig, sessionCache);
    return {
        getSession,
        touchSession,
        updateSession,
        getAccessToken,
        withApiAuthRequired,
        withPageAuthRequired,
        handleLogin,
        handleLogout,
        handleCallback,
        handleBackchannelLogout,
        handleProfile,
        handleAuth,
        withMiddlewareAuthRequired
    };
};
exports._initAuth = _initAuth;
//# sourceMappingURL=init.js.map