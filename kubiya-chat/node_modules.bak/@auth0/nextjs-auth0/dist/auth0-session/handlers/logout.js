"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const tslib_1 = require("tslib");
const url_join_1 = tslib_1.__importDefault(require("url-join"));
const debug_1 = tslib_1.__importDefault(require("../utils/debug"));
const debug = (0, debug_1.default)('logout');
function logoutHandlerFactory(getConfig, getClient, sessionCache) {
    const getConfigFn = typeof getConfig === 'function' ? getConfig : () => getConfig;
    return async (req, res, options = {}) => {
        const config = await getConfigFn(req);
        const client = await getClient(config);
        let returnURL = options.returnTo || config.routes.postLogoutRedirect;
        debug('logout() with return url: %s', returnURL);
        try {
            new URL(returnURL);
        }
        catch (_) {
            returnURL = (0, url_join_1.default)(config.baseURL, returnURL);
        }
        const isAuthenticated = await sessionCache.isAuthenticated(req.req, res.res);
        if (!isAuthenticated) {
            debug('end-user already logged out, redirecting to %s', returnURL);
            res.redirect(returnURL);
            return;
        }
        const idToken = await sessionCache.getIdToken(req.req, res.res);
        await sessionCache.delete(req.req, res.res);
        if (!config.idpLogout) {
            debug('performing a local only logout, redirecting to %s', returnURL);
            res.redirect(returnURL);
            return;
        }
        returnURL = await client.endSessionUrl(Object.assign(Object.assign({}, options.logoutParams), { post_logout_redirect_uri: returnURL, id_token_hint: idToken }));
        debug('logging out of identity provider, redirecting to %s', returnURL);
        res.redirect(returnURL);
    };
}
exports.default = logoutHandlerFactory;
//# sourceMappingURL=logout.js.map