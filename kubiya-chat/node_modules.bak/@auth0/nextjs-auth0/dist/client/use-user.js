"use strict";
'use client';
Object.defineProperty(exports, "__esModule", { value: true });
exports.useUser = exports.UserContext = exports.RequestError = void 0;
const tslib_1 = require("tslib");
const react_1 = tslib_1.__importStar(require("react"));
const use_config_1 = tslib_1.__importDefault(require("./use-config"));
/**
 * The error thrown by the default {@link UserFetcher}.
 *
 * The `status` property contains the status code of the response. It is `0` when the request
 * fails, for example due to being offline.
 *
 * This error is not thrown when the status code of the response is `204`, because that means the
 * user is not authenticated.
 *
 * @category Client
 */
class RequestError extends Error {
    constructor(status) {
        /* c8 ignore next */
        super();
        this.status = status;
        Object.setPrototypeOf(this, RequestError.prototype);
    }
}
exports.RequestError = RequestError;
/**
 * @ignore
 */
const missingUserProvider = 'You forgot to wrap your app in <UserProvider>';
/**
 * @ignore
 */
exports.UserContext = (0, react_1.createContext)({
    get user() {
        throw new Error(missingUserProvider);
    },
    get error() {
        throw new Error(missingUserProvider);
    },
    get isLoading() {
        throw new Error(missingUserProvider);
    },
    checkSession: () => {
        throw new Error(missingUserProvider);
    }
});
/**
 * The `useUser` hook, which will get you the {@link UserProfile} object from the server-side session by fetching it
 * from the {@link HandleProfile} API route.
 *
 * ```js
 * // pages/profile.js
 * import Link from 'next/link';
 * import { useUser } from '@auth0/nextjs-auth0/client';
 *
 * export default function Profile() {
 *   const { user, error, isLoading } = useUser();
 *
 *   if (isLoading) return <div>Loading...</div>;
 *   if (error) return <div>{error.message}</div>;
 *   if (!user) return <Link href="/api/auth/login"><a>Login</a></Link>;
 *   return <div>Hello {user.name}, <Link href="/api/auth/logout"><a>Logout</a></Link></div>;
 * }
 * ```
 *
 * @category Client
 */
const useUser = () => (0, react_1.useContext)(exports.UserContext);
exports.useUser = useUser;
/**
 * @ignore
 */
const userFetcher = async (url) => {
    let response;
    try {
        response = await fetch(url);
    }
    catch (_a) {
        throw new RequestError(0); // Network error
    }
    if (response.status == 204)
        return undefined;
    if (response.ok)
        return response.json();
    throw new RequestError(response.status);
};
exports.default = ({ children, user: initialUser, profileUrl = process.env.NEXT_PUBLIC_AUTH0_PROFILE || '/api/auth/me', loginUrl, fetcher = userFetcher }) => {
    const [state, setState] = (0, react_1.useState)({ user: initialUser, isLoading: !initialUser });
    const checkSession = (0, react_1.useCallback)(async () => {
        try {
            const user = await fetcher(profileUrl);
            setState((previous) => (Object.assign(Object.assign({}, previous), { user, error: undefined })));
        }
        catch (error) {
            setState((previous) => (Object.assign(Object.assign({}, previous), { error: error })));
        }
    }, [profileUrl]);
    (0, react_1.useEffect)(() => {
        if (state.user)
            return;
        (async () => {
            await checkSession();
            setState((previous) => (Object.assign(Object.assign({}, previous), { isLoading: false })));
        })();
    }, [state.user]);
    const { user, error, isLoading } = state;
    const value = (0, react_1.useMemo)(() => ({ user, error, isLoading, checkSession }), [user, error, isLoading, checkSession]);
    return (react_1.default.createElement(use_config_1.default, { loginUrl: loginUrl },
        react_1.default.createElement(exports.UserContext.Provider, { value: value }, children)));
};
//# sourceMappingURL=use-user.js.map