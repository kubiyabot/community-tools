"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const server_1 = require("next/server");
const session_1 = require("../session");
const assert_1 = require("../utils/assert");
const req_helpers_1 = require("../utils/req-helpers");
/**
 * @ignore
 */
function withApiAuthFactory(sessionCache) {
    const pageRouteHandler = pageRouteHandlerFactory(sessionCache);
    const appRouteHandler = appRouteHandlerFactory(sessionCache);
    return (apiRoute) => (req, resOrParams) => {
        if ((0, req_helpers_1.isRequest)(req)) {
            return appRouteHandler(apiRoute)(req, resOrParams);
        }
        return pageRouteHandler(apiRoute)(req, resOrParams);
    };
}
exports.default = withApiAuthFactory;
/**
 * @ignore
 */
const appRouteHandlerFactory = (sessionCache) => (apiRoute) => async (req, params) => {
    const res = new server_1.NextResponse();
    const [session] = await (0, session_1.get)({ sessionCache, req, res });
    if (!session || !session.user) {
        return server_1.NextResponse.json({ error: 'not_authenticated', description: 'The user does not have an active session or is not authenticated' }, { status: 401 });
    }
    const apiRes = await apiRoute(req, params);
    const nextApiRes = apiRes instanceof server_1.NextResponse ? apiRes : new server_1.NextResponse(apiRes.body, apiRes);
    for (const cookie of res.cookies.getAll()) {
        if (!nextApiRes.cookies.get(cookie.name)) {
            nextApiRes.cookies.set(cookie);
        }
    }
    return nextApiRes;
};
/**
 * @ignore
 */
const pageRouteHandlerFactory = (sessionCache) => (apiRoute) => async (req, res) => {
    (0, assert_1.assertReqRes)(req, res);
    const session = await sessionCache.get(req, res);
    if (!session || !session.user) {
        res.status(401).json({
            error: 'not_authenticated',
            description: 'The user does not have an active session or is not authenticated'
        });
        return;
    }
    await apiRoute(req, res);
};
//# sourceMappingURL=with-api-auth-required.js.map