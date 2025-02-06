"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const server_1 = require("next/server");
const http_1 = require("../http");
const router_helpers_1 = require("./router-helpers");
/**
 * @ignore
 */
function handleBackchannelLogoutFactory(handler, getConfig) {
    const appRouteHandler = appRouteHandlerFactory(handler, getConfig);
    const pageRouteHandler = pageRouteHandlerFactory(handler, getConfig);
    return (0, router_helpers_1.getHandler)(appRouteHandler, pageRouteHandler);
}
exports.default = handleBackchannelLogoutFactory;
const appRouteHandlerFactory = (handler, getConfig) => async (req) => {
    try {
        const auth0Req = new http_1.Auth0NextRequest(req);
        const config = await getConfig(auth0Req);
        if (!config.backchannelLogout) {
            return new server_1.NextResponse('Back-Channel Logout is not enabled.', { status: 404 });
        }
        const auth0Res = new http_1.Auth0NextResponse(new server_1.NextResponse());
        await handler(auth0Req, auth0Res);
        return auth0Res.res;
    }
    catch (e) {
        return server_1.NextResponse.json({
            error: e.code || 'unknown_error',
            error_description: e.description || e.message
        }, { status: 400, headers: { 'cache-control': 'no-store' } });
    }
};
const pageRouteHandlerFactory = (handler, getConfig) => async (req, res) => {
    try {
        const auth0Req = new http_1.Auth0NextApiRequest(req);
        const config = await getConfig(auth0Req);
        if (!config.backchannelLogout) {
            res.status(404).end('Back-Channel Logout is not enabled.');
            return;
        }
        return await handler(auth0Req, new http_1.Auth0NextApiResponse(res));
    }
    catch (e) {
        res.setHeader('cache-control', 'no-store');
        res.status(400).json({
            error: e.code || 'unknown_error',
            error_description: e.description || e.message
        });
    }
};
//# sourceMappingURL=backchannel-logout.js.map