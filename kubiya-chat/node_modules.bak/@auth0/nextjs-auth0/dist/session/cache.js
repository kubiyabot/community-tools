"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.set = exports.get = exports.getAuth0ReqRes = void 0;
const auth0_session_1 = require("../auth0-session");
const session_1 = require("./session");
const http_1 = require("../auth0-session/http");
const http_2 = require("../http");
const req_helpers_1 = require("../utils/req-helpers");
const getAuth0ReqRes = (req, res) => {
    if ((0, req_helpers_1.isRequest)(req)) {
        return [new http_2.Auth0NextRequest(req), new http_2.Auth0NextResponse(res)];
    }
    if ((0, req_helpers_1.isNextApiRequest)(req)) {
        return [new http_2.Auth0NextApiRequest(req), new http_2.Auth0NextApiResponse(res)];
    }
    return [new http_1.NodeRequest(req), new http_1.NodeResponse(res)];
};
exports.getAuth0ReqRes = getAuth0ReqRes;
class SessionCache {
    constructor(getConfig) {
        this.getConfig = getConfig;
        this.cache = new WeakMap();
        this.iatCache = new WeakMap();
    }
    getSessionStore(config) {
        if (!this.sessionStore) {
            this.sessionStore = config.session.store
                ? new auth0_session_1.StatefulSession(config)
                : new auth0_session_1.StatelessSession(config);
        }
        return this.sessionStore;
    }
    async init(req, res, autoSave = true) {
        if (!this.cache.has(req)) {
            const [auth0Req] = (0, exports.getAuth0ReqRes)(req, res);
            const config = await this.getConfig(auth0Req);
            const sessionStore = this.getSessionStore(config);
            const [json, iat] = await sessionStore.read(auth0Req);
            const session = (0, session_1.fromJson)(json);
            if (session && config.backchannelLogout && (await (0, auth0_session_1.isLoggedOut)(session.user, config))) {
                this.cache.set(req, null);
                await this.save(req, res);
            }
            else {
                this.iatCache.set(req, iat);
                this.cache.set(req, session);
                if (config.session.rolling && config.session.autoSave && autoSave) {
                    await this.save(req, res);
                }
            }
        }
    }
    async save(req, res) {
        const [auth0Req, auth0Res] = (0, exports.getAuth0ReqRes)(req, res);
        const config = await this.getConfig(auth0Req);
        const sessionStore = this.getSessionStore(config);
        await sessionStore.save(auth0Req, auth0Res, this.cache.get(req), this.iatCache.get(req));
    }
    async create(req, res, session) {
        const [auth0Req] = (0, exports.getAuth0ReqRes)(req, res);
        const config = await this.getConfig(auth0Req);
        if (config.backchannelLogout) {
            await (0, auth0_session_1.deleteSub)(session.user.sub, config);
        }
        this.cache.set(req, session);
        await this.save(req, res);
    }
    async delete(req, res) {
        await this.init(req, res, false);
        this.cache.set(req, null);
        await this.save(req, res);
    }
    async isAuthenticated(req, res) {
        await this.init(req, res);
        const session = this.cache.get(req);
        return !!(session === null || session === void 0 ? void 0 : session.user);
    }
    async getIdToken(req, res) {
        await this.init(req, res);
        const session = this.cache.get(req);
        return session === null || session === void 0 ? void 0 : session.idToken;
    }
    async set(req, res, session) {
        await this.init(req, res, false);
        this.cache.set(req, session);
        await this.save(req, res);
    }
    async get(req, res) {
        await this.init(req, res);
        return this.cache.get(req);
    }
    async fromTokenEndpointResponse(req, res, tokenSet) {
        const [auth0Req] = (0, exports.getAuth0ReqRes)(req, res);
        const config = await this.getConfig(auth0Req);
        return (0, session_1.fromTokenEndpointResponse)(tokenSet, config);
    }
}
exports.default = SessionCache;
const get = async ({ sessionCache, req, res }) => {
    if (req && res) {
        return [await sessionCache.get(req, res)];
    }
    const auth0Req = new http_2.Auth0NextRequestCookies();
    const config = await sessionCache.getConfig(auth0Req);
    const sessionStore = sessionCache.getSessionStore(config);
    const { session: { rolling, autoSave } } = config;
    const [json, iat] = await sessionStore.read(auth0Req);
    const session = (0, session_1.fromJson)(json);
    if (session && config.backchannelLogout && (await (0, auth0_session_1.isLoggedOut)(session.user, config))) {
        await (0, exports.set)({ session: null, sessionCache });
        return [];
    }
    else {
        if (rolling && autoSave) {
            await (0, exports.set)({ session, sessionCache, iat });
        }
        return [session, iat];
    }
};
exports.get = get;
const set = async ({ session, sessionCache, iat, req, res }) => {
    if (req && res) {
        return sessionCache.set(req, res, session);
    }
    const auth0Req = new http_2.Auth0NextRequestCookies();
    const config = await sessionCache.getConfig(auth0Req);
    const sessionStore = sessionCache.getSessionStore(config);
    await sessionStore.save(auth0Req, new http_2.Auth0NextResponseCookies(), session, iat);
};
exports.set = set;
//# sourceMappingURL=cache.js.map