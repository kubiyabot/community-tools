import { NextApiResponse, NextApiRequest } from 'next';
import { NextRequest } from 'next/server';
import { SessionCache, Session, GetAccessToken } from '../session';
import { AuthHandler, Handler, OptionsProvider } from './router-helpers';
import { GetClient } from '../auth0-session/client/abstract-client';
import { GetConfig } from '../config';
/**
 * After refetch handler for page router {@link AfterRefetchPageRoute} and app router {@link AfterRefetchAppRoute}.
 *
 * @category Server
 */
export type AfterRefetch = AfterRefetchPageRoute | AfterRefetchAppRoute;
/**
 * After refetch handler for page router.
 *
 * @category Server
 */
export type AfterRefetchPageRoute = (req: NextApiRequest, res: NextApiResponse, session: Session) => Promise<Session> | Session;
/**
 * After refetch handler for app router.
 *
 * @category Server
 */
export type AfterRefetchAppRoute = (req: NextRequest, session: Session) => Promise<Session> | Session;
/**
 * Options to customize the profile handler.
 *
 * @see {@link HandleProfile}
 *
 * @category Server
 */
export type ProfileOptions = {
    /**
     * If set to `true` this will refetch the user profile information from `/userinfo` and save it
     * to the session.
     */
    refetch?: boolean;
    /**
     * Like {@link AfterCallback}  and {@link AfterRefresh} when a session is created, you can use
     * this function to validate or add/remove claims after the session is updated. Will only run if
     * {@link ProfileOptions.refetch} is `true`.
     */
    afterRefetch?: AfterRefetch;
};
/**
 * Options provider for the default profile handler.
 * Use this to generate options that depend on values from the request.
 *
 * @category Server
 */
export type ProfileOptionsProvider = OptionsProvider<ProfileOptions>;
/**
 * Use this to customize the default profile handler without overriding it.
 * You can still override the handler if needed.
 *
 * @example Pass an options object
 *
 * ```js
 * // pages/api/auth/[auth0].js
 * import { handleAuth, handleProfile } from '@auth0/nextjs-auth0';
 *
 * export default handleAuth({
 *   profile: handleProfile({ refetch: true })
 * });
 * ```
 *
 * @example Pass a function that receives the request and returns an options object
 *
 * ```js
 * // pages/api/auth/[auth0].js
 * import { handleAuth, handleProfile } from '@auth0/nextjs-auth0';
 *
 * export default handleAuth({
 *   profile: handleProfile((req) => {
 *     return { refetch: true };
 *   })
 * });
 * ```
 *
 * This is useful for generating options that depend on values from the request.
 *
 * @example Override the profile handler
 *
 * ```js
 * import { handleAuth, handleProfile } from '@auth0/nextjs-auth0';
 *
 * export default handleAuth({
 *   profile: async (req, res) => {
 *     try {
 *       await handleProfile(req, res, { refetch: true });
 *     } catch (error) {
 *       console.error(error);
 *     }
 *   }
 * });
 * ```
 *
 * @category Server
 */
export type HandleProfile = AuthHandler<ProfileOptions>;
/**
 * The handler for the `/api/auth/me` API route.
 *
 * @throws {@link HandlerError}
 *
 * @category Server
 */
export type ProfileHandler = Handler<ProfileOptions>;
/**
 * @ignore
 */
export default function profileHandler(getConfig: GetConfig, getClient: GetClient, getAccessToken: GetAccessToken, sessionCache: SessionCache): HandleProfile;
//# sourceMappingURL=profile.d.ts.map