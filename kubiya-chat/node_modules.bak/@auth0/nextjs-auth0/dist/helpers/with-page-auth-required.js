"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const session_1 = require("../session");
const assert_1 = require("../utils/assert");
const http_1 = require("../http");
const http_2 = require("../auth0-session/http");
/**
 * @ignore
 */
function withPageAuthRequiredFactory(getConfig, sessionCache) {
    const appRouteHandler = appRouteHandlerFactory(getConfig, sessionCache);
    const pageRouteHandler = pageRouteHandlerFactory(getConfig, sessionCache);
    return ((fnOrOpts, opts) => {
        if (typeof fnOrOpts === 'function') {
            return appRouteHandler(fnOrOpts, opts);
        }
        return pageRouteHandler(fnOrOpts);
    });
}
exports.default = withPageAuthRequiredFactory;
/**
 * @ignore
 */
const appRouteHandlerFactory = (getConfig, sessionCache) => (handler, opts = {}) => async (params) => {
    const { routes: { login: loginUrl } } = await getConfig(new http_1.Auth0NextRequestCookies());
    const [session] = await (0, session_1.get)({ sessionCache });
    if (!(session === null || session === void 0 ? void 0 : session.user)) {
        const returnTo = typeof opts.returnTo === 'function' ? await opts.returnTo(params) : opts.returnTo;
        // eslint-disable-next-line @typescript-eslint/no-var-requires
        const { redirect } = require('next/navigation');
        redirect(`${loginUrl}${opts.returnTo ? `?returnTo=${returnTo}` : ''}`);
    }
    return handler(params);
};
/**
 * @ignore
 */
const pageRouteHandlerFactory = (getConfig, sessionCache) => ({ getServerSideProps, returnTo } = {}) => async (ctx) => {
    (0, assert_1.assertCtx)(ctx);
    const { routes: { login: loginUrl } } = await getConfig(new http_2.NodeRequest(ctx.req));
    const session = await sessionCache.get(ctx.req, ctx.res);
    if (!(session === null || session === void 0 ? void 0 : session.user)) {
        return {
            redirect: {
                destination: `${loginUrl}?returnTo=${encodeURIComponent(returnTo || ctx.resolvedUrl)}`,
                permanent: false
            }
        };
    }
    let ret = { props: {} };
    if (getServerSideProps) {
        ret = await getServerSideProps(ctx);
    }
    if (ret.props instanceof Promise) {
        return Object.assign(Object.assign({}, ret), { props: ret.props.then((props) => (Object.assign({ user: session.user }, props))) });
    }
    return Object.assign(Object.assign({}, ret), { props: Object.assign({ user: session.user }, ret.props) });
};
//# sourceMappingURL=with-page-auth-required.js.map