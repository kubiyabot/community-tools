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
function handleCallbackFactory(handler, getConfig) {
    const appRouteHandler = appRouteHandlerFactory(handler, getConfig);
    const pageRouteHandler = pageRouteHandlerFactory(handler, getConfig);
    return (0, router_helpers_1.getHandler)(appRouteHandler, pageRouteHandler);
}
exports.default = handleCallbackFactory;
const applyOptions = (req, res, options, config) => {
    const opts = Object.assign({}, options);
    const idTokenValidator = (afterCallback, organization) => (session, state) => {
        if (organization) {
            if (organization.startsWith('org_')) {
                if (!session.user.org_id) {
                    throw new Error('Organization Id (org_id) claim must be a string present in the ID token');
                }
                if (session.user.org_id !== organization) {
                    throw new Error(`Organization Id (org_id) claim value mismatch in the ID token; ` +
                        `expected "${organization}", found "${session.user.org_id}"`);
                }
            }
            else {
                if (!session.user.org_name) {
                    throw new Error('Organization Name (org_name) claim must be a string present in the ID token');
                }
                if (session.user.org_name !== organization.toLowerCase()) {
                    throw new Error(`Organization Name (org_name) claim value mismatch in the ID token; ` +
                        `expected "${organization}", found "${session.user.org_name}"`);
                }
            }
        }
        if (afterCallback) {
            if (res) {
                return afterCallback(req, res, session, state);
            }
            else {
                return afterCallback(req, session, state);
            }
        }
        return session;
    };
    return Object.assign(Object.assign({}, opts), { afterCallback: idTokenValidator(opts.afterCallback, opts.organization || config.organization) });
};
/**
 * @ignore
 */
const appRouteHandlerFactory = (handler, getConfig) => async (req, _ctx, options = {}) => {
    try {
        const auth0Req = new http_1.Auth0NextRequest(req);
        const nextConfig = await getConfig(auth0Req);
        const auth0Res = new http_1.Auth0NextResponse(new server_1.NextResponse());
        await handler(auth0Req, auth0Res, applyOptions(req, undefined, options, nextConfig));
        return auth0Res.res;
    }
    catch (e) {
        throw new errors_1.CallbackHandlerError(e);
    }
};
/**
 * @ignore
 */
const pageRouteHandlerFactory = (handler, getConfig) => async (req, res, options = {}) => {
    try {
        const auth0Req = new http_1.Auth0NextApiRequest(req);
        const nextConfig = await getConfig(auth0Req);
        (0, assert_1.assertReqRes)(req, res);
        return await handler(auth0Req, new http_1.Auth0NextApiResponse(res), applyOptions(req, res, options, nextConfig));
    }
    catch (e) {
        throw new errors_1.CallbackHandlerError(e);
    }
};
//# sourceMappingURL=callback.js.map