"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getHandler = void 0;
const req_helpers_1 = require("../utils/req-helpers");
const getHandler = (appRouteHandler, pageRouteHandler) => (reqOrOptions, resOrCtx, options) => {
    if ((0, req_helpers_1.isRequest)(reqOrOptions)) {
        return appRouteHandler(reqOrOptions, resOrCtx, options);
    }
    if ('socket' in reqOrOptions) {
        return pageRouteHandler(reqOrOptions, resOrCtx, options);
    }
    return (req, resOrCtxInner) => {
        const opts = (typeof reqOrOptions === 'function' ? reqOrOptions(req) : reqOrOptions);
        if ((0, req_helpers_1.isRequest)(req)) {
            return appRouteHandler(req, resOrCtxInner, opts);
        }
        return pageRouteHandler(req, resOrCtxInner, opts);
    };
};
exports.getHandler = getHandler;
//# sourceMappingURL=router-helpers.js.map