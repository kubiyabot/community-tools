"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const http_1 = require("../auth0-session/http");
let warned = false;
const warn = () => {
    /* c8 ignore next 8 */
    if (process.env.NODE_ENV === 'development' && !warned) {
        console.warn('nextjs-auth0 is attempting to set cookies from a server component,' +
            'see https://github.com/auth0/nextjs-auth0#using-this-sdk-with-react-server-components');
        warned = true;
    }
};
class Auth0NextResponseCookies extends http_1.Auth0ResponseCookies {
    constructor() {
        super();
    }
    setCookie(name, value, options) {
        // eslint-disable-next-line @typescript-eslint/no-var-requires
        const { cookies } = require('next/headers');
        const cookieSetter = cookies();
        try {
            cookieSetter.set(Object.assign(Object.assign({}, options), { name, value }));
        }
        catch (_) {
            warn();
        }
    }
    clearCookie(name, options) {
        // eslint-disable-next-line @typescript-eslint/no-var-requires
        const { cookies } = require('next/headers');
        const cookieSetter = cookies();
        try {
            cookieSetter.set(Object.assign(Object.assign({}, options), { name, value: '', expires: new Date(0) }));
        }
        catch (_) {
            warn();
        }
    }
}
exports.default = Auth0NextResponseCookies;
//# sourceMappingURL=auth0-next-response-cookies.js.map