"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const server_1 = require("next/server");
const http_1 = require("../http");
/**
 * @ignore
 */
function withMiddlewareAuthRequiredFactory(getConfig, sessionCache) {
    return function withMiddlewareAuthRequired(opts) {
        return async function wrappedMiddleware(...args) {
            const [req] = args;
            const { routes: { login, callback } } = await getConfig(new http_1.Auth0NextRequest(req));
            let middleware;
            const { pathname, origin, search } = req.nextUrl;
            let returnTo = `${pathname}${search}`;
            if (typeof opts === 'function') {
                middleware = opts;
            }
            else if (opts) {
                middleware = opts.middleware;
                returnTo = (typeof opts.returnTo === 'function' ? await opts.returnTo(req) : opts.returnTo) || returnTo;
            }
            const ignorePaths = [login, callback, '/_next', '/favicon.ico'];
            if (ignorePaths.some((p) => pathname.startsWith(p))) {
                return;
            }
            const authRes = server_1.NextResponse.next();
            const session = await sessionCache.get(req, authRes);
            if (!(session === null || session === void 0 ? void 0 : session.user)) {
                if (pathname.startsWith('/api')) {
                    return server_1.NextResponse.json({
                        error: 'not_authenticated',
                        description: 'The user does not have an active session or is not authenticated'
                    }, { status: 401 });
                }
                return server_1.NextResponse.redirect(new URL(`${login}?returnTo=${encodeURIComponent(returnTo)}`, origin));
            }
            const res = await (middleware && middleware(...args));
            if (res) {
                const nextRes = new server_1.NextResponse(res.body, res);
                const cookies = authRes.cookies.getAll();
                if ('cookies' in res) {
                    for (const cookie of res.cookies.getAll()) {
                        nextRes.cookies.set(cookie);
                    }
                }
                for (const cookie of cookies) {
                    if (!nextRes.cookies.get(cookie.name)) {
                        nextRes.cookies.set(cookie);
                    }
                }
                return nextRes;
            }
            else {
                return authRes;
            }
        };
    };
}
exports.default = withMiddlewareAuthRequiredFactory;
//# sourceMappingURL=with-middleware-auth-required.js.map