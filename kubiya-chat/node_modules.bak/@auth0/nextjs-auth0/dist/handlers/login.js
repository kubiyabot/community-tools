"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const tslib_1 = require("tslib");
const server_1 = require("next/server");
const url_helpers_1 = tslib_1.__importDefault(require("../utils/url-helpers"));
const assert_1 = require("../utils/assert");
const errors_1 = require("../utils/errors");
const http_1 = require("../http");
const router_helpers_1 = require("./router-helpers");
/**
 * @ignore
 */
function handleLoginFactory(handler, getConfig) {
    const appRouteHandler = appRouteHandlerFactory(handler, getConfig);
    const pageRouteHandler = pageRouteHandlerFactory(handler, getConfig);
    return (0, router_helpers_1.getHandler)(appRouteHandler, pageRouteHandler);
}
exports.default = handleLoginFactory;
/**
 * @ignore
 */
const applyOptions = (req, options, dangerousReturnTo, config) => {
    var _a;
    let opts;
    let getLoginState;
    // eslint-disable-next-line prefer-const
    ({ getLoginState } = options, opts = tslib_1.__rest(options, ["getLoginState"]));
    if (dangerousReturnTo) {
        const safeBaseUrl = new URL(((_a = options.authorizationParams) === null || _a === void 0 ? void 0 : _a.redirect_uri) || config.baseURL);
        const returnTo = (0, url_helpers_1.default)(dangerousReturnTo, safeBaseUrl);
        opts = Object.assign(Object.assign({}, opts), { returnTo });
    }
    if (config.organization) {
        opts = Object.assign(Object.assign({}, opts), { authorizationParams: Object.assign({ organization: config.organization }, opts.authorizationParams) });
    }
    if (getLoginState) {
        opts.getLoginState = (_opts) => getLoginState(req, _opts);
    }
    return opts;
};
/**
 * @ignore
 */
const appRouteHandlerFactory = (handler, getConfig) => async (req, _ctx, options = {}) => {
    try {
        const auth0Req = new http_1.Auth0NextRequest(req);
        const config = await getConfig(auth0Req);
        const url = new URL(req.url);
        const dangerousReturnTo = url.searchParams.get('returnTo');
        const auth0Res = new http_1.Auth0NextResponse(new server_1.NextResponse());
        await handler(auth0Req, auth0Res, applyOptions(req, options, dangerousReturnTo, config));
        return auth0Res.res;
    }
    catch (e) {
        throw new errors_1.LoginHandlerError(e);
    }
};
/**
 * @ignore
 */
const pageRouteHandlerFactory = (handler, getConfig) => async (req, res, options = {}) => {
    try {
        const auth0Req = new http_1.Auth0NextApiRequest(req);
        const config = await getConfig(auth0Req);
        (0, assert_1.assertReqRes)(req, res);
        const dangerousReturnTo = req.query.returnTo && Array.isArray(req.query.returnTo) ? req.query.returnTo[0] : req.query.returnTo;
        return await handler(auth0Req, new http_1.Auth0NextApiResponse(res), applyOptions(req, options, dangerousReturnTo, config));
    }
    catch (e) {
        throw new errors_1.LoginHandlerError(e);
    }
};
//# sourceMappingURL=login.js.map