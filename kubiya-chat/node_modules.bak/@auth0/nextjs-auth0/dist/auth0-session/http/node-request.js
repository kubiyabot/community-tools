"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const tslib_1 = require("tslib");
const cookie_1 = require("cookie");
const auth0_request_1 = tslib_1.__importDefault(require("./auth0-request"));
class NodeRequest extends auth0_request_1.default {
    constructor(req) {
        /* c8 ignore next */
        super(req);
        this.req = req;
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
        return (0, cookie_1.parse)(this.req.headers.cookie || '');
    }
}
exports.default = NodeRequest;
//# sourceMappingURL=node-request.js.map