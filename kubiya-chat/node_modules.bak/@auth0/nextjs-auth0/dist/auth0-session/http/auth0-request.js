"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const tslib_1 = require("tslib");
const auth0_request_cookies_1 = tslib_1.__importDefault(require("./auth0-request-cookies"));
class Auth0Request extends auth0_request_cookies_1.default {
    constructor(req) {
        super();
        this.req = req;
    }
}
exports.default = Auth0Request;
//# sourceMappingURL=auth0-request.js.map