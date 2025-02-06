"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const http_1 = require("../auth0-session/http");
class Auth0NextRequestCookies extends http_1.Auth0RequestCookies {
    constructor() {
        super();
    }
    getCookies() {
        // eslint-disable-next-line @typescript-eslint/no-var-requires
        const { cookies } = require('next/headers');
        const cookieStore = cookies();
        return cookieStore.getAll().reduce((memo, { name, value }) => (Object.assign(Object.assign({}, memo), { [name]: value })), {});
    }
}
exports.default = Auth0NextRequestCookies;
//# sourceMappingURL=auth0-next-request-cookies.js.map