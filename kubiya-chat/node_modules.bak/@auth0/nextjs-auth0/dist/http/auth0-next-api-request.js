"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const http_1 = require("../auth0-session/http");
class Auth0NextApiRequest extends http_1.Auth0Request {
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
    getBody() {
        return this.req.body;
    }
    getCookies() {
        return this.req.cookies;
    }
}
exports.default = Auth0NextApiRequest;
//# sourceMappingURL=auth0-next-api-request.js.map