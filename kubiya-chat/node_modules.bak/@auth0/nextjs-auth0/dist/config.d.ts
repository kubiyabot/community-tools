import type { Config as BaseConfig } from './auth0-session/config';
import { DeepPartial } from './auth0-session/get-config';
import type { Auth0Request, Auth0RequestCookies } from './auth0-session/http';
/**
 * @category server
 */
export interface NextConfig extends BaseConfig {
    /**
     * Log users in to a specific organization.
     *
     * This will specify an `organization` parameter in your user's login request and will add a step to validate
     * the `org_id` or `org_name` claim in your user's ID token.
     *
     * If your app supports multiple organizations, you should take a look at {@link AuthorizationParams.organization}.
     */
    organization?: string;
    routes: BaseConfig['routes'] & {
        login: string;
    };
}
/**
 * ## Configuration properties.
 *
 * The Server part of the SDK can be configured in 2 ways.
 *
 * ### 1. Environment Variables
 *
 * The simplest way to use the SDK is to use the named exports ({@link HandleAuth}, {@link HandleLogin},
 * {@link HandleLogout}, {@link HandleCallback}, {@link HandleProfile}, {@link GetSession}, {@link GetAccessToken},
 * {@link WithApiAuthRequired}, and {@link WithPageAuthRequired}).
 *
 * ```js
 * // pages/api/auth/[auth0].js
 * import { handleAuth } from '@auth0/nextjs-auth0';
 *
 * return handleAuth();
 * ```
 *
 * When you use these named exports, an instance of the SDK is created for you which you can configure using
 * environment variables:
 *
 * ### Required
 *
 * - `AUTH0_SECRET`: See {@link BaseConfig.secret}.
 * - `AUTH0_ISSUER_BASE_URL`: See {@link BaseConfig.issuerBaseURL}.
 * - `AUTH0_BASE_URL`: See {@link BaseConfig.baseURL}.
 * - `AUTH0_CLIENT_ID`: See {@link BaseConfig.clientID}.
 * - `AUTH0_CLIENT_SECRET`: See {@link BaseConfig.clientSecret}.
 *
 * ### Optional
 *
 * - `AUTH0_CLOCK_TOLERANCE`: See {@link BaseConfig.clockTolerance}.
 * - `AUTH0_HTTP_TIMEOUT`: See {@link BaseConfig.httpTimeout}.
 * - `AUTH0_ENABLE_TELEMETRY`: See {@link BaseConfig.enableTelemetry}.
 * - `AUTH0_IDP_LOGOUT`: See {@link BaseConfig.idpLogout}.
 * - `AUTH0_ID_TOKEN_SIGNING_ALG`: See {@link BaseConfig.idTokenSigningAlg}.
 * - `AUTH0_LEGACY_SAME_SITE_COOKIE`: See {@link BaseConfig.legacySameSiteCookie}.
 * - `AUTH0_IDENTITY_CLAIM_FILTER`: See {@link BaseConfig.identityClaimFilter}.
 * - `AUTH0_PUSHED_AUTHORIZATION_REQUESTS` See {@link BaseConfig.pushedAuthorizationRequests}.
 * - `NEXT_PUBLIC_AUTH0_LOGIN`: See {@link NextConfig.routes}.
 * - `AUTH0_CALLBACK`: See {@link BaseConfig.routes}.
 * - `AUTH0_POST_LOGOUT_REDIRECT`: See {@link BaseConfig.routes}.
 * - `AUTH0_AUDIENCE`: See {@link BaseConfig.authorizationParams}.
 * - `AUTH0_SCOPE`: See {@link BaseConfig.authorizationParams}.
 * - `AUTH0_ORGANIZATION`: See {@link NextConfig.organization}.
 * - `AUTH0_SESSION_NAME`: See {@link SessionConfig.name}.
 * - `AUTH0_SESSION_ROLLING`: See {@link SessionConfig.rolling}.
 * - `AUTH0_SESSION_ROLLING_DURATION`: See {@link SessionConfig.rollingDuration}.
 * - `AUTH0_SESSION_ABSOLUTE_DURATION`: See {@link SessionConfig.absoluteDuration}.
 * - `AUTH0_SESSION_AUTO_SAVE`: See {@link SessionConfig.autoSave}.
 * - `AUTH0_COOKIE_DOMAIN`: See {@link CookieConfig.domain}.
 * - `AUTH0_COOKIE_PATH`: See {@link CookieConfig.path}.
 * - `AUTH0_COOKIE_TRANSIENT`: See {@link CookieConfig.transient}.
 * - `AUTH0_COOKIE_HTTP_ONLY`: See {@link CookieConfig.httpOnly}.
 * - `AUTH0_COOKIE_SECURE`: See {@link CookieConfig.secure}.
 * - `AUTH0_COOKIE_SAME_SITE`: See {@link CookieConfig.sameSite}.
 * - `AUTH0_CLIENT_ASSERTION_SIGNING_KEY`: See {@link BaseConfig.clientAssertionSigningKey}
 * - `AUTH0_CLIENT_ASSERTION_SIGNING_ALG`: See {@link BaseConfig.clientAssertionSigningAlg}
 * - `AUTH0_TRANSACTION_COOKIE_NAME` See {@link BaseConfig.transactionCookie}
 * - `AUTH0_TRANSACTION_COOKIE_DOMAIN` See {@link BaseConfig.transactionCookie}
 * - `AUTH0_TRANSACTION_COOKIE_PATH` See {@link BaseConfig.transactionCookie}
 * - `AUTH0_TRANSACTION_COOKIE_SAME_SITE` See {@link BaseConfig.transactionCookie}
 * - `AUTH0_TRANSACTION_COOKIE_SECURE` See {@link BaseConfig.transactionCookie}
 *
 * ### 2. Create your own instance using {@link InitAuth0}
 *
 * If you don't want to configure the SDK with environment variables or you want more fine grained control over the
 * instance, you can create an instance yourself and use the handlers and helpers from that.
 *
 * First, export your configured instance from another module:
 *
 * ```js
 * // utils/auth0.js
 * import { initAuth0 } from '@auth0/nextjs-auth0';
 *
 * export default initAuth0({ ...ConfigParameters... });
 * ```
 *
 * Then import it into your route handler:
 *
 * ```js
 * // pages/api/auth/[auth0].js
 * import auth0 from '../../../../utils/auth0';
 *
 * export default auth0.handleAuth();
 * ```
 *
 * **IMPORTANT** If you use {@link InitAuth0}, you should *not* use the other named exports as they will use a different
 * instance of the SDK. Also note - this is for the server side part of the SDK - you will always use named exports for
 * the front end components: {@link UserProvider}, {@link UseUser} and the
 * front end version of {@link WithPageAuthRequired}
 *
 * @category Server
 */
export type ConfigParameters = DeepPartial<NextConfig>;
/**
 * @ignore
 */
export declare const getConfig: (params?: ConfigParameters) => NextConfig;
export type GetConfig = (req: Auth0Request | Auth0RequestCookies) => Promise<NextConfig> | NextConfig;
export declare const configSingletonGetter: (params: DeepPartial<NextConfig> | undefined, genId: () => string) => GetConfig;
//# sourceMappingURL=config.d.ts.map