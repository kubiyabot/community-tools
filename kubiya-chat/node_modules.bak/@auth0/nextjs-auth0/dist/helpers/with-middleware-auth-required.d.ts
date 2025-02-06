import { NextMiddleware, NextRequest } from 'next/server';
import { SessionCache } from '../session';
import { GetConfig } from '../config';
/**
 * Pass custom options to {@link WithMiddlewareAuthRequired}.
 *
 * @category Server
 */
export type WithMiddlewareAuthRequiredOptions = {
    middleware?: NextMiddleware;
    returnTo?: string | ((req: NextRequest) => Promise<string> | string);
};
/**
 * Protect your pages with Next.js Middleware. For example:
 *
 * To protect all your routes:
 *
 * ```js
 * // middleware.js
 * import { withMiddlewareAuthRequired } from '@auth0/nextjs-auth0/edge';
 *
 * export default withMiddlewareAuthRequired();
 * ```
 *
 * To protect specific routes:
 *
 * ```js
 * // middleware.js
 * import { withMiddlewareAuthRequired } from '@auth0/nextjs-auth0/edge';
 *
 * export default withMiddlewareAuthRequired();
 *
 * export const config = {
 *   matcher: '/about/:path*',
 * };
 * ```
 * For more info see: https://nextjs.org/docs/advanced-features/middleware#matching-paths
 *
 * To run custom middleware for authenticated users:
 *
 * ```js
 * // middleware.js
 * import { withMiddlewareAuthRequired, getSession } from '@auth0/nextjs-auth0/edge';
 *
 * export default withMiddlewareAuthRequired(async function middleware(req) {
 *   const res = NextResponse.next();
 *   const user = await getSession(req, res);
 *   res.cookies.set('hl', user.language);
 *   return res;
 * });
 * ```
 *
 * To provide a custom `returnTo` url to login:
 *
 * ```js
 * // middleware.js
 * import { withMiddlewareAuthRequired, getSession } from '@auth0/nextjs-auth0/edge';
 *
 * export default withMiddlewareAuthRequired({
 *   returnTo: '/foo',
 *   // Custom middleware is provided with the `middleware` config option
 *   async middleware(req) { return NextResponse.next(); }
 * });
 * ```
 *
 * You can also provide a method for `returnTo` that takes the req as an argument.
 *
 * ```js
 * // middleware.js
 * import { withMiddlewareAuthRequired, getSession } from '@auth0/nextjs-auth0/edge';
 *
 * export default withMiddlewareAuthRequired({
 *   returnTo(req) { return `${req.nextURL.basePath}${req.nextURL.pathname}`};
 * });
 * ```
 *
 * @category Server
 */
export type WithMiddlewareAuthRequired = (middlewareOrOpts?: NextMiddleware | WithMiddlewareAuthRequiredOptions) => NextMiddleware;
/**
 * @ignore
 */
export default function withMiddlewareAuthRequiredFactory(getConfig: GetConfig, sessionCache: SessionCache): WithMiddlewareAuthRequired;
//# sourceMappingURL=with-middleware-auth-required.d.ts.map