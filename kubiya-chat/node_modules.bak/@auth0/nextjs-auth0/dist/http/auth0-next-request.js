"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const http_1 = require("../auth0-session/http");
class Auth0NextRequest extends http_1.Auth0Request {
    constructor(req) {
        /* c8 ignore next */
        super(req);
    }
    getUrl() {
        return this.req.url;
    }
    getMethod() {
        return this.req.method;
    }
    async getBody() {
        return this.req.text();
    }
    getCookies() {
        const { cookies } = this.req;
        if (typeof cookies.getAll === 'function') {
            return this.req.cookies.getAll().reduce((memo, { name, value }) => (Object.assign(Object.assign({}, memo), { [name]: value })), {});
        }
        // Edge cookies before Next 13.0.1 have no `getAll` and extend `Map`.
        const legacyCookies = cookies;
        return Array.from(legacyCookies.keys()).reduce((memo, key) => {
            memo[key] = legacyCookies.get(key);
            return memo;
        }, {});
    }
}
exports.default = Auth0NextRequest;
//# sourceMappingURL=auth0-next-request.js.map