import { Auth0Server, ConfigParameters, GetAccessToken, GetSession, HandleAuth, HandleCallback, HandleLogin, HandleLogout, HandleProfile, TouchSession, UpdateSession, WithApiAuthRequired, WithPageAuthRequired } from './shared';
import { WithMiddlewareAuthRequired } from './helpers/with-middleware-auth-required';
/**
 * Initialise your own instance of the SDK.
 *
 * See {@link ConfigParameters}.
 *
 * @category Server
 */
export type InitAuth0 = (params?: ConfigParameters) => Auth0Server;
export declare const initAuth0: InitAuth0;
export declare const getSession: GetSession;
export declare const updateSession: UpdateSession;
export declare const getAccessToken: GetAccessToken;
export declare const touchSession: TouchSession;
export declare const withApiAuthRequired: WithApiAuthRequired;
export declare const withPageAuthRequired: WithPageAuthRequired;
export declare const handleLogin: HandleLogin;
export declare const handleLogout: HandleLogout;
export declare const handleCallback: HandleCallback;
export declare const handleProfile: HandleProfile;
export declare const handleAuth: HandleAuth;
export declare const withMiddlewareAuthRequired: WithMiddlewareAuthRequired;
export * from './shared';
//# sourceMappingURL=edge.d.ts.map