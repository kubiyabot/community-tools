"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const server_1 = require("next/server");
const session_1 = require("../session");
const assert_1 = require("../utils/assert");
const errors_1 = require("../utils/errors");
const router_helpers_1 = require("./router-helpers");
const http_1 = require("../http");
/**
 * @ignore
 */
function profileHandler(getConfig, getClient, getAccessToken, sessionCache) {
    const appRouteHandler = appRouteHandlerFactory(getConfig, getClient, getAccessToken, sessionCache);
    const pageRouteHandler = pageRouteHandlerFactory(getConfig, getClient, getAccessToken, sessionCache);
    return (0, router_helpers_1.getHandler)(appRouteHandler, pageRouteHandler);
}
exports.default = profileHandler;
/**
 * @ignore
 */
const appRouteHandlerFactory = (getConfig, getClient, getAccessToken, sessionCache) => async (req, _ctx, options = {}) => {
    try {
        const config = await getConfig(new http_1.Auth0NextRequest(req));
        const client = await getClient(config);
        const res = new server_1.NextResponse();
        if (!(await sessionCache.isAuthenticated(req, res))) {
            const emptyRes = new server_1.NextResponse(null, { status: 204 });
            res.headers.forEach((val, key) => emptyRes.headers.set(key, val));
            return emptyRes;
        }
        const session = (await sessionCache.get(req, res));
        res.headers.set('Cache-Control', 'no-store');
        if (options.refetch) {
            const { accessToken } = await getAccessToken(req, res);
            if (!accessToken) {
                throw new Error('No access token available to refetch the profile');
            }
            const userInfo = await client.userinfo(accessToken);
            let newSession = (0, session_1.fromJson)(Object.assign(Object.assign({}, session), { user: Object.assign(Object.assign({}, session.user), userInfo) }));
            if (options.afterRefetch) {
                newSession = await options.afterRefetch(req, newSession);
            }
            await sessionCache.set(req, res, newSession);
            return server_1.NextResponse.json(newSession.user, res);
        }
        return server_1.NextResponse.json(session.user, res);
    }
    catch (e) {
        throw new errors_1.ProfileHandlerError(e);
    }
};
/**
 * @ignore
 */
const pageRouteHandlerFactory = (getConfig, getClient, getAccessToken, sessionCache) => async (req, res, options = {}) => {
    try {
        (0, assert_1.assertReqRes)(req, res);
        const config = await getConfig(new http_1.Auth0NextApiRequest(req));
        const client = await getClient(config);
        if (!(await sessionCache.isAuthenticated(req, res))) {
            res.status(204).end();
            return;
        }
        const session = (await sessionCache.get(req, res));
        res.setHeader('Cache-Control', 'no-store');
        if (options.refetch) {
            const { accessToken } = await getAccessToken(req, res);
            if (!accessToken) {
                throw new Error('No access token available to refetch the profile');
            }
            const userInfo = await client.userinfo(accessToken);
            let newSession = (0, session_1.fromJson)(Object.assign(Object.assign({}, session), { user: Object.assign(Object.assign({}, session.user), userInfo) }));
            if (options.afterRefetch) {
                newSession = await options.afterRefetch(req, res, newSession);
            }
            await sessionCache.set(req, res, newSession);
            res.json(newSession.user);
            return;
        }
        res.json(session.user);
    }
    catch (e) {
        throw new errors_1.ProfileHandlerError(e);
    }
};
//# sourceMappingURL=profile.js.map