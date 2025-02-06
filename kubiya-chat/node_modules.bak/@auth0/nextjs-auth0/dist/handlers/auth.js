"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const tslib_1 = require("tslib");
const req_helpers_1 = require("../utils/req-helpers");
/**
 * @ignore
 */
const defaultPageRouterOnError = (_req, res, error) => {
    console.error(error);
    res.status(error.status || 500).end();
};
/**
 * @ignore
 */
const defaultAppRouterOnError = (_req, error) => {
    console.error(error);
};
/**
 * @ignore
 */
function handlerFactory({ handleLogin, handleLogout, handleCallback, handleProfile, handleBackchannelLogout }) {
    return (_a = {}) => {
        var { onError } = _a, handlers = tslib_1.__rest(_a, ["onError"]);
        const customHandlers = Object.assign({ login: handleLogin, logout: handleLogout, callback: handleCallback, 'backchannel-logout': handleBackchannelLogout, me: handlers.profile || handleProfile }, handlers);
        const appRouteHandler = appRouteHandlerFactory(customHandlers, onError);
        const pageRouteHandler = pageRouteHandlerFactory(customHandlers, onError);
        return (req, resOrCtx) => {
            if ((0, req_helpers_1.isRequest)(req)) {
                return appRouteHandler(req, resOrCtx);
            }
            return pageRouteHandler(req, resOrCtx);
        };
    };
}
exports.default = handlerFactory;
/**
 * @ignore
 */
const appRouteHandlerFactory = (customHandlers, onError) => async (req, ctx) => {
    const { params } = ctx;
    let route = params.auth0;
    if (Array.isArray(route)) {
        let otherRoutes;
        [route, ...otherRoutes] = route;
        if (otherRoutes.length) {
            return new Response(null, { status: 404 });
        }
    }
    const handler = route && customHandlers.hasOwnProperty(route) && customHandlers[route];
    try {
        if (handler) {
            return await handler(req, ctx);
        }
        else {
            return new Response(null, { status: 404 });
        }
    }
    catch (error) {
        const res = await (onError || defaultAppRouterOnError)(req, error);
        return res || new Response(null, { status: error.status || 500 });
    }
};
/**
 * @ignore
 */
const pageRouteHandlerFactory = (customHandlers, onError) => async (req, res) => {
    let { query: { auth0: route } } = req;
    if (Array.isArray(route)) {
        let otherRoutes;
        [route, ...otherRoutes] = route;
        if (otherRoutes.length) {
            res.status(404).end();
            return;
        }
    }
    try {
        const handler = route && customHandlers.hasOwnProperty(route) && customHandlers[route];
        if (handler) {
            await handler(req, res);
        }
        else {
            res.status(404).end();
        }
    }
    catch (error) {
        await (onError || defaultPageRouterOnError)(req, res, error);
        if (!res.writableEnded) {
            // 200 is the default, so we assume it has not been set in the custom error handler if it equals 200
            res.status(res.statusCode === 200 ? 500 : res.statusCode).end();
        }
    }
};
//# sourceMappingURL=auth.js.map