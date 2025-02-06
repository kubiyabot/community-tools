"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.StatelessSession = void 0;
const tslib_1 = require("tslib");
const jose = tslib_1.__importStar(require("jose"));
const cookie_1 = require("cookie");
const debug_1 = tslib_1.__importDefault(require("../utils/debug"));
const hkdf_1 = require("../utils/hkdf");
const abstract_session_1 = require("./abstract-session");
const debug = (0, debug_1.default)('stateless-session');
const MAX_COOKIE_SIZE = 4096;
const alg = 'dir';
const enc = 'A256GCM';
const notNull = (value) => value !== null;
class StatelessSession extends abstract_session_1.AbstractSession {
    constructor(config) {
        super(config);
        this.config = config;
    }
    async getChunkSize(config) {
        if (this.chunkSize === undefined) {
            const _a = config.session, _b = _a.cookie, { transient } = _b, cookieConfig = tslib_1.__rest(_b, ["transient"]), { name: sessionName } = _a;
            const cookieOptions = Object.assign({}, cookieConfig);
            if (!transient) {
                cookieOptions.expires = new Date();
            }
            const emptyCookie = (0, cookie_1.serialize)(`${sessionName}.0`, '', cookieOptions);
            this.chunkSize = MAX_COOKIE_SIZE - emptyCookie.length;
        }
        return this.chunkSize;
    }
    async getKeys(config) {
        if (!this.keys) {
            const secret = config.secret;
            const secrets = Array.isArray(secret) ? secret : [secret];
            this.keys = await Promise.all(secrets.map(hkdf_1.encryption));
        }
        return this.keys;
    }
    async encrypt(payload, { iat, uat, exp }, key) {
        return await new jose.EncryptJWT(Object.assign({}, payload)).setProtectedHeader({ alg, enc, uat, iat, exp }).encrypt(key);
    }
    async decrypt(jwe, keys) {
        let err;
        for (const key of keys) {
            try {
                return await jose.jwtDecrypt(jwe, key);
            }
            catch (e) {
                err = e;
            }
        }
        throw err;
    }
    async getSession(req) {
        const config = await this.getConfig(req);
        const { name: sessionName } = config.session;
        const cookies = req.getCookies();
        let existingSessionValue;
        if (sessionName in cookies) {
            // get JWE from un-chunked session cookie
            debug('reading session from %s cookie', sessionName);
            existingSessionValue = cookies[sessionName];
        }
        else if (`${sessionName}.0` in cookies) {
            // get JWE from chunked session cookie
            // iterate all cookie names
            // match and filter for the ones that match sessionName.<number>
            // sort by chunk index
            // concat
            existingSessionValue = Object.entries(cookies)
                .map(([cookie, value]) => {
                const match = cookie.match(`^${sessionName}\\.(\\d+)$`);
                if (match) {
                    return [match[1], value];
                }
                return null;
            })
                .filter(notNull)
                .sort(([a], [b]) => {
                return parseInt(a, 10) - parseInt(b, 10);
            })
                .map(([i, chunk]) => {
                debug('reading session chunk from %s.%d cookie', sessionName, i);
                return chunk;
            })
                .join('');
        }
        if (existingSessionValue) {
            const keys = await this.getKeys(config);
            const { protectedHeader, payload } = await this.decrypt(existingSessionValue, keys);
            return { header: protectedHeader, data: payload };
        }
        return;
    }
    async setSession(req, res, session, uat, iat, exp, cookieOptions) {
        const config = await this.getConfig(req);
        const { name: sessionName } = config.session;
        const cookies = req.getCookies();
        debug('found session, creating signed session cookie(s) with name %o(.i)', sessionName);
        const [key] = await this.getKeys(config);
        const value = await this.encrypt(session, { iat, uat, exp }, key);
        const chunkSize = await this.getChunkSize(config);
        const chunkCount = Math.ceil(value.length / chunkSize);
        const existingCookies = new Set(Object.keys(cookies).filter((cookie) => cookie.match(`^${sessionName}(?:\\.\\d)?$`)));
        if (chunkCount > 1) {
            debug('cookie size greater than %d, chunking', this.chunkSize);
            for (let i = 0; i < chunkCount; i++) {
                const chunkValue = value.slice(i * chunkSize, (i + 1) * chunkSize);
                const chunkCookieName = `${sessionName}.${i}`;
                res.setCookie(chunkCookieName, chunkValue, cookieOptions);
                existingCookies.delete(chunkCookieName);
            }
        }
        else {
            res.setCookie(sessionName, value, cookieOptions);
            existingCookies.delete(sessionName);
        }
        // When the number of chunks changes due to the cookie size changing,
        // you need to delete any obsolete cookies.
        existingCookies.forEach((cookie) => res.clearCookie(cookie, cookieOptions));
    }
    async deleteSession(req, res, cookieOptions) {
        const config = await this.getConfig(req);
        const { name: sessionName } = config.session;
        const cookies = req.getCookies();
        for (const cookieName of Object.keys(cookies)) {
            if (cookieName.match(`^${sessionName}(?:\\.\\d)?$`)) {
                res.clearCookie(cookieName, cookieOptions);
            }
        }
    }
}
exports.StatelessSession = StatelessSession;
//# sourceMappingURL=stateless-session.js.map