"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.StatefulSession = void 0;
const tslib_1 = require("tslib");
const debug_1 = tslib_1.__importDefault(require("../utils/debug"));
const abstract_session_1 = require("./abstract-session");
const signed_cookies_1 = require("../utils/signed-cookies");
const hkdf_1 = require("../utils/hkdf");
const debug = (0, debug_1.default)('stateful-session');
class StatefulSession extends abstract_session_1.AbstractSession {
    async getStore(config) {
        if (!this.store) {
            this.store = config.session.store;
        }
        return this.store;
    }
    async getKeys(config) {
        if (!this.keys) {
            const secret = config.secret;
            const secrets = Array.isArray(secret) ? secret : [secret];
            this.keys = await Promise.all(secrets.map(hkdf_1.signing));
        }
        return this.keys;
    }
    async getSession(req) {
        const config = await this.getConfig(req);
        const { name: sessionName } = config.session;
        const cookies = req.getCookies();
        const keys = await this.getKeys(config);
        const sessionId = await (0, signed_cookies_1.getCookieValue)(sessionName, cookies[sessionName], keys);
        if (sessionId) {
            const store = await this.getStore(config);
            debug('reading session from %s store', sessionId);
            return store.get(sessionId);
        }
        return;
    }
    async setSession(req, res, session, uat, iat, exp, cookieOptions, isNewSession) {
        const config = await this.getConfig(req);
        const store = await this.getStore(config);
        const { name: sessionName, genId } = config.session;
        const cookies = req.getCookies();
        const keys = await this.getKeys(config);
        let sessionId = await (0, signed_cookies_1.getCookieValue)(sessionName, cookies[sessionName], keys);
        // If this is a new session created by a new login we need to remove the old session
        // from the store and regenerate the session id to prevent session fixation issue.
        if (sessionId && isNewSession) {
            debug('regenerating session id %o to prevent session fixation', sessionId);
            await store.delete(sessionId);
            sessionId = undefined;
        }
        if (!sessionId) {
            sessionId = await genId(req, session);
            debug('generated new session id %o', sessionId);
        }
        debug('set session %o', sessionId);
        const cookieValue = await (0, signed_cookies_1.generateCookieValue)(sessionName, sessionId, keys[0]);
        res.setCookie(sessionName, cookieValue, cookieOptions);
        await store.set(sessionId, {
            header: { iat, uat, exp },
            data: session
        });
    }
    async deleteSession(req, res, cookieOptions) {
        const config = await this.getConfig(req);
        const { name: sessionName } = config.session;
        const cookies = req.getCookies();
        const keys = await this.getKeys(config);
        const sessionId = await (0, signed_cookies_1.getCookieValue)(sessionName, cookies[sessionName], keys);
        if (sessionId) {
            const store = await this.getStore(config);
            debug('deleting session %o', sessionId);
            res.clearCookie(sessionName, cookieOptions);
            await store.delete(sessionId);
        }
    }
}
exports.StatefulSession = StatefulSession;
//# sourceMappingURL=stateful-session.js.map