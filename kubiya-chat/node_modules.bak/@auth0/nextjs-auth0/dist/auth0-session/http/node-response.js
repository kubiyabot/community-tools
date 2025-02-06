"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const tslib_1 = require("tslib");
const cookie_1 = require("cookie");
const auth0_response_1 = tslib_1.__importDefault(require("./auth0-response"));
const errors_1 = require("../utils/errors");
class NodeResponse extends auth0_response_1.default {
    constructor(res) {
        /* c8 ignore next */
        super(res);
        this.res = res;
    }
    setCookie(name, value, options) {
        let cookies = this.res.getHeader('Set-Cookie') || [];
        if (!Array.isArray(cookies)) {
            cookies = [cookies];
        }
        this.res.setHeader('Set-Cookie', [
            ...cookies.filter((cookie) => !cookie.startsWith(`${name}=`)),
            (0, cookie_1.serialize)(name, value, options)
        ]);
    }
    redirect(location, status = 302) {
        if (this.res.writableEnded) {
            return;
        }
        this.res.writeHead(status, {
            Location: this.res.getHeader('Location') || location
        });
        this.res.end((0, errors_1.htmlSafe)(location));
    }
    send204() {
        this.res.statusCode = 204;
        this.res.end();
    }
    setHeader(name, value) {
        this.res.setHeader(name, value);
    }
}
exports.default = NodeResponse;
//# sourceMappingURL=node-response.js.map