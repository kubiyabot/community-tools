"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
class Auth0ResponseCookies {
    clearCookie(name, options = {}) {
        const { domain, path, secure, sameSite } = options;
        const clearOptions = {
            domain,
            path,
            maxAge: 0
        };
        // If SameSite=None is set, the cookie Secure attribute must also be set (or the cookie will be blocked)
        // https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite#none
        if (sameSite === 'none') {
            clearOptions.secure = secure;
            clearOptions.sameSite = sameSite;
        }
        this.setCookie(name, '', clearOptions);
    }
}
exports.default = Auth0ResponseCookies;
//# sourceMappingURL=auth0-response-cookies.js.map