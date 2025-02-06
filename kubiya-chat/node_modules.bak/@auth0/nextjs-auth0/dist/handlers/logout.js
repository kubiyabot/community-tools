"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const server_1 = require("next/server");
const assert_1 = require("../utils/assert");
const errors_1 = require("../utils/errors");
const http_1 = require("../http");
const router_helpers_1 = require("./router-helpers");
/**
 * @ignore
 */
function handleLogoutFactory(handler) {
    const appRouteHandler = appRouteHandlerFactory(handler);
    const pageRouteHandler = pageRouteHandlerFactory(handler);
    return (0, router_helpers_1.getHandler)(appRouteHandler, pageRouteHandler);
}
exports.default = handleLogoutFactory;
const appRouteHandlerFactory = (handler) => async (req, _ctx, options = {}) => {
    try {
        const auth0Res = new http_1.Auth0NextResponse(new server_1.NextResponse());
        await handler(new http_1.Auth0NextRequest(req), auth0Res, options);
        return auth0Res.res;
    }
    catch (e) {
        throw new errors_1.LogoutHandlerError(e);
    }
};
const pageRouteHandlerFactory = (handler) => async (req, res, options = {}) => {
    try {
        (0, assert_1.assertReqRes)(req, res);
        return await handler(new http_1.Auth0NextApiRequest(req), new http_1.Auth0NextApiResponse(res), options);
    }
    catch (e) {
        throw new errors_1.LogoutHandlerError(e);
    }
};
//# sourceMappingURL=logout.js.map