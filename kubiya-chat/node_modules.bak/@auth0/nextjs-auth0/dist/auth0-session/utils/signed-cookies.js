"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.generateCookieValue = exports.getCookieValue = void 0;
const tslib_1 = require("tslib");
const jose = tslib_1.__importStar(require("jose"));
const getCookieValue = async (k, v, keys) => {
    if (!v) {
        return undefined;
    }
    const [value, signature] = v.split('.');
    const flattenedJWS = {
        protected: jose.base64url.encode(JSON.stringify({ alg: 'HS256', b64: false, crit: ['b64'] })),
        payload: `${k}=${value}`,
        signature
    };
    for (const key of keys) {
        try {
            await jose.flattenedVerify(flattenedJWS, key, {
                algorithms: ['HS256']
            });
            return value;
        }
        catch (e) { }
    }
    return;
};
exports.getCookieValue = getCookieValue;
const generateCookieValue = async (cookie, value, key) => {
    const { signature } = await new jose.FlattenedSign(new TextEncoder().encode(`${cookie}=${value}`))
        .setProtectedHeader({ alg: 'HS256', b64: false, crit: ['b64'] })
        .sign(key);
    return `${value}.${signature}`;
};
exports.generateCookieValue = generateCookieValue;
//# sourceMappingURL=signed-cookies.js.map