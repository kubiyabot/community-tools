"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const tslib_1 = require("tslib");
const auth0_response_cookies_1 = tslib_1.__importDefault(require("./auth0-response-cookies"));
class Auth0Response extends auth0_response_cookies_1.default {
    constructor(res) {
        super();
        this.res = res;
    }
}
exports.default = Auth0Response;
//# sourceMappingURL=auth0-response.js.map