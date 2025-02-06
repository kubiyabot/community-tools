"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const signed_cookies_1 = require("./utils/signed-cookies");
const hkdf_1 = require("./utils/hkdf");
class TransientStore {
    constructor(getConfig) {
        this.getConfig = typeof getConfig === 'function' ? getConfig : () => getConfig;
    }
    async getKeys(config) {
        if (!this.keys) {
            const secret = config.secret;
            const secrets = Array.isArray(secret) ? secret : [secret];
            this.keys = await Promise.all(secrets.map(hkdf_1.signing));
        }
        return this.keys;
    }
    /**
     * Set a cookie with a value or a generated nonce.
     *
     * @param {String} key Cookie name to use.
     * @param {IncomingMessage} req Server Request object.
     * @param {ServerResponse} res Server Response object.
     * @param {Object} opts Options object.
     * @param {String} opts.sameSite SameSite attribute of `None`, `Lax`, or `Strict`. Defaults to `None`.
     * @param {String} opts.value Cookie value. Omit this key to store a generated value.
     *
     * @return {String} Cookie value that was set.
     */
    async save(key, req, res, { sameSite = 'none', value }) {
        const isSameSiteNone = sameSite === 'none';
        const config = await this.getConfig(req);
        const { domain, path, secure } = config.transactionCookie;
        const basicAttr = {
            httpOnly: true,
            secure,
            domain,
            path
        };
        const [signingKey] = await this.getKeys(config);
        {
            const cookieValue = await (0, signed_cookies_1.generateCookieValue)(key, value, signingKey);
            // Set the cookie with the SameSite attribute and, if needed, the Secure flag.
            res.setCookie(key, cookieValue, Object.assign(Object.assign({}, basicAttr), { sameSite, secure: isSameSiteNone ? true : basicAttr.secure }));
        }
        if (isSameSiteNone && config.legacySameSiteCookie) {
            const cookieValue = await (0, signed_cookies_1.generateCookieValue)(`_${key}`, value, signingKey);
            // Set the fallback cookie with no SameSite or Secure attributes.
            res.setCookie(`_${key}`, cookieValue, basicAttr);
        }
        return value;
    }
    /**
     * Get a cookie value then delete it.
     *
     * @param {String} key Cookie name to use.
     * @param {IncomingMessage} req Express Request object.
     * @param {ServerResponse} res Express Response object.
     *
     * @return {String|undefined} Cookie value or undefined if cookie was not found.
     */
    async read(key, req, res) {
        const cookies = req.getCookies();
        const cookie = cookies[key];
        const config = await this.getConfig(req);
        const cookieConfig = config.transactionCookie;
        const verifyingKeys = await this.getKeys(config);
        let value = await (0, signed_cookies_1.getCookieValue)(key, cookie, verifyingKeys);
        res.clearCookie(key, cookieConfig);
        if (config.legacySameSiteCookie) {
            const fallbackKey = `_${key}`;
            if (!value) {
                const fallbackCookie = cookies[fallbackKey];
                value = await (0, signed_cookies_1.getCookieValue)(fallbackKey, fallbackCookie, verifyingKeys);
            }
            res.clearCookie(fallbackKey, cookieConfig);
        }
        return value;
    }
}
exports.default = TransientStore;
//# sourceMappingURL=transient-store.js.map