"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.deleteSub = exports.isLoggedOut = void 0;
const tslib_1 = require("tslib");
const logout_token_verifier_1 = tslib_1.__importDefault(require("../utils/logout-token-verifier"));
const errors_1 = require("../utils/errors");
const getStore = (config) => {
    const { session: { store }, backchannelLogout } = config;
    return typeof backchannelLogout === 'boolean' ? store : backchannelLogout.store;
};
function backchannelLogoutHandlerFactory(getConfig, getClient) {
    const getConfigFn = typeof getConfig === 'function' ? getConfig : () => getConfig;
    const verifyLogoutToken = (0, logout_token_verifier_1.default)();
    return async (req, res) => {
        const config = await getConfigFn(req);
        const client = await getClient(config);
        res.setHeader('cache-control', 'no-store');
        const body = new URLSearchParams(await req.getBody());
        const logoutToken = body.get('logout_token');
        if (!logoutToken) {
            throw new errors_1.BackchannelLogoutError('invalid_request', 'Missing Logout Token');
        }
        let token;
        try {
            token = await verifyLogoutToken(logoutToken, config, await client.getIssuerMetadata());
        }
        catch (e) {
            throw new errors_1.BackchannelLogoutError('invalid_request', e.message);
        }
        const { clientID, session: { absoluteDuration, rolling: rollingEnabled, rollingDuration } } = config;
        const store = getStore(config);
        const maxAge = (rollingEnabled
            ? Math.min(absoluteDuration, rollingDuration)
            : absoluteDuration) * 1000;
        const now = (Date.now() / 1000) | 0;
        const payload = {
            header: { iat: now, uat: now, exp: now + maxAge, maxAge },
            data: {}
        };
        try {
            const { sid, sub } = token;
            await Promise.all([
                sid && store.set(`sid|${clientID}|${sid}`, payload),
                sub && store.set(`sub|${clientID}|${sub}`, payload)
            ]);
        }
        catch (e) {
            throw new errors_1.BackchannelLogoutError('application_error', e.message);
        }
        res.send204();
    };
}
exports.default = backchannelLogoutHandlerFactory;
const isLoggedOut = async (user, config) => {
    const { clientID } = config;
    const store = getStore(config);
    const { sid, sub } = user;
    const [logoutSid, logoutSub] = await Promise.all([
        store.get(`sid|${clientID}|${sid}`),
        store.get(`sub|${clientID}|${sub}`)
    ]);
    return !!(logoutSid || logoutSub);
};
exports.isLoggedOut = isLoggedOut;
const deleteSub = async (sub, config) => {
    const { clientID } = config;
    const store = getStore(config);
    await store.delete(`sub|${clientID}|${sub}`);
};
exports.deleteSub = deleteSub;
//# sourceMappingURL=backchannel-logout.js.map