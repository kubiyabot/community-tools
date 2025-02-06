"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AbstractSession = void 0;
const tslib_1 = require("tslib");
const debug_1 = tslib_1.__importDefault(require("../utils/debug"));
const debug = (0, debug_1.default)('session');
const epoch = () => (Date.now() / 1000) | 0; // eslint-disable-line no-bitwise
const assert = (bool, msg) => {
    if (!bool) {
        throw new Error(msg);
    }
};
class AbstractSession {
    constructor(getConfig) {
        this.getConfig = typeof getConfig === 'function' ? getConfig : () => getConfig;
    }
    async read(req) {
        const config = await this.getConfig(req);
        const { rollingDuration, absoluteDuration } = config.session;
        try {
            const existingSessionValue = await this.getSession(req);
            if (existingSessionValue) {
                const { header, data } = existingSessionValue;
                const { iat, uat, exp } = header;
                // check that the existing session isn't expired based on options when it was established
                assert(exp > epoch(), 'it is expired based on options when it was established');
                // check that the existing session isn't expired based on current rollingDuration rules
                if (rollingDuration) {
                    assert(uat + rollingDuration > epoch(), 'it is expired based on current rollingDuration rules');
                }
                // check that the existing session isn't expired based on current absoluteDuration rules
                if (typeof absoluteDuration === 'number') {
                    assert(iat + absoluteDuration > epoch(), 'it is expired based on current absoluteDuration rules');
                }
                return [data, iat];
            }
        }
        catch (err) {
            debug('error handling session %O', err);
        }
        return [];
    }
    async save(req, res, session, createdAt) {
        const config = await this.getConfig(req);
        const _a = config.session.cookie, { transient } = _a, cookieConfig = tslib_1.__rest(_a, ["transient"]);
        if (!session) {
            await this.deleteSession(req, res, cookieConfig);
            return;
        }
        const isNewSession = typeof createdAt === 'undefined';
        const uat = epoch();
        const iat = typeof createdAt === 'number' ? createdAt : uat;
        const exp = this.calculateExp(iat, uat, config);
        const cookieOptions = Object.assign({}, cookieConfig);
        if (!transient) {
            cookieOptions.expires = new Date(exp * 1000);
        }
        await this.setSession(req, res, session, uat, iat, exp, cookieOptions, isNewSession);
    }
    calculateExp(iat, uat, config) {
        const { absoluteDuration } = config.session;
        const { rolling, rollingDuration } = config.session;
        if (typeof absoluteDuration !== 'number') {
            return uat + rollingDuration;
        }
        if (!rolling) {
            return iat + absoluteDuration;
        }
        return Math.min(uat + rollingDuration, iat + absoluteDuration);
    }
}
exports.AbstractSession = AbstractSession;
//# sourceMappingURL=abstract-session.js.map