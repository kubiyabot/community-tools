import { CookieSerializeOptions } from 'cookie';
export default abstract class Auth0ResponseCookies {
    abstract setCookie(name: string, value: string, options?: CookieSerializeOptions): void;
    clearCookie(name: string, options?: CookieSerializeOptions): void;
}
//# sourceMappingURL=auth0-response-cookies.d.ts.map