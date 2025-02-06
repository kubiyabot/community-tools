"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const server_1 = require("next/server");
const http_1 = require("../auth0-session/http");
class Auth0NextResponse extends http_1.Auth0Response {
    constructor(res) {
        /* c8 ignore next */
        super(res);
    }
    setCookie(name, value, options) {
        this.res.cookies.set(name, value, options);
    }
    clearCookie(name, options) {
        this.setCookie(name, '', Object.assign(Object.assign({}, options), { expires: new Date(0) }));
    }
    redirect(location, status = 302) {
        const oldRes = this.res;
        this.res = new server_1.NextResponse(null, { status });
        oldRes.headers.forEach((value, key) => {
            this.res.headers.set(key, value);
        });
        this.res.headers.set('location', location);
        for (const cookie of oldRes.cookies.getAll()) {
            this.res.cookies.set(cookie);
        }
    }
    setHeader(name, value) {
        this.res.headers.set(name, value);
    }
    send204() {
        const oldRes = this.res;
        this.res = new server_1.NextResponse(null, { status: 204 });
        oldRes.headers.forEach((value, key) => {
            this.res.headers.set(key, value);
        });
    }
}
exports.default = Auth0NextResponse;
//# sourceMappingURL=auth0-next-response.js.map