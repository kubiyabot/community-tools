"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.generateSessionCookie = void 0;
const tslib_1 = require("tslib");
const auth0_session_1 = require("../auth0-session");
const generateSessionCookie = async (session, config) => {
    const weekInSeconds = 7 * 24 * 60 * 60;
    const { secret, duration: absoluteDuration = weekInSeconds } = config, cookie = tslib_1.__rest(config, ["secret", "duration"]);
    const cookieStoreConfig = { secret, session: { absoluteDuration, cookie } };
    const cookieStore = new auth0_session_1.StatelessSession(cookieStoreConfig);
    const epoch = (Date.now() / 1000) | 0;
    const [key] = await cookieStore.getKeys(cookieStoreConfig);
    return cookieStore.encrypt(session, { iat: epoch, uat: epoch, exp: epoch + absoluteDuration }, key);
};
exports.generateSessionCookie = generateSessionCookie;
//# sourceMappingURL=testing.js.map