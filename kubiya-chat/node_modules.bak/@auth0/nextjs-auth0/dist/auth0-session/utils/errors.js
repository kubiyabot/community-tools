"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.htmlSafe = exports.BackchannelLogoutError = exports.UserInfoError = exports.DiscoveryError = exports.IdentityProviderError = exports.ApplicationError = exports.MissingStateCookieError = exports.MalformedStateCookieError = exports.MissingStateParamError = exports.EscapedError = void 0;
class EscapedError extends Error {
    /**
     * **WARNING** The message can contain user input and is only escaped using basic escaping for putting untrusted data
     * directly into the HTML body
     */
    constructor(message) {
        /* c8 ignore next */
        super(htmlSafe(message));
        Object.setPrototypeOf(this, EscapedError.prototype);
    }
}
exports.EscapedError = EscapedError;
class MissingStateParamError extends Error {
    constructor() {
        /* c8 ignore next */
        super(MissingStateParamError.message);
        this.status = 400;
        this.statusCode = 400;
        Object.setPrototypeOf(this, MissingStateParamError.prototype);
    }
}
exports.MissingStateParamError = MissingStateParamError;
MissingStateParamError.message = 'Missing state parameter in Authorization Response.';
class MalformedStateCookieError extends Error {
    constructor() {
        /* c8 ignore next */
        super(MalformedStateCookieError.message);
        this.status = 400;
        this.statusCode = 400;
        Object.setPrototypeOf(this, MalformedStateCookieError.prototype);
    }
}
exports.MalformedStateCookieError = MalformedStateCookieError;
MalformedStateCookieError.message = 'Your state cookie is not valid JSON.';
class MissingStateCookieError extends Error {
    constructor() {
        /* c8 ignore next */
        super(MissingStateCookieError.message);
        this.status = 400;
        this.statusCode = 400;
        Object.setPrototypeOf(this, MissingStateCookieError.prototype);
    }
}
exports.MissingStateCookieError = MissingStateCookieError;
MissingStateCookieError.message = 'Missing state cookie from login request (check login URL, callback URL and cookie config).';
class ApplicationError extends EscapedError {
    /**
     * **WARNING** The message can contain user input and is only escaped using basic escaping for putting untrusted data
     * directly into the HTML body
     */
    constructor(rpError) {
        /* c8 ignore next */
        super(rpError.message);
        Object.setPrototypeOf(this, ApplicationError.prototype);
    }
}
exports.ApplicationError = ApplicationError;
class IdentityProviderError extends EscapedError {
    /**
     * **WARNING** The message can contain user input and is only escaped using basic escaping for putting untrusted data
     * directly into the HTML body
     */
    constructor(rpError) {
        /* c8 ignore next */
        super(rpError.message);
        this.error = htmlSafe(rpError.error);
        this.errorDescription = htmlSafe(rpError.error_description);
        Object.setPrototypeOf(this, IdentityProviderError.prototype);
    }
}
exports.IdentityProviderError = IdentityProviderError;
class DiscoveryError extends EscapedError {
    constructor(error, issuerBaseUrl) {
        /* c8 ignore next */
        super(`Discovery requests failing for ${issuerBaseUrl}, ${error.message}`);
        Object.setPrototypeOf(this, DiscoveryError.prototype);
    }
}
exports.DiscoveryError = DiscoveryError;
class UserInfoError extends EscapedError {
    constructor(msg) {
        /* c8 ignore next */
        super(`Userinfo request failing with: ${msg}`);
        Object.setPrototypeOf(this, UserInfoError.prototype);
    }
}
exports.UserInfoError = UserInfoError;
class BackchannelLogoutError extends Error {
    constructor(code, description) {
        /* c8 ignore next */
        super(description);
        this.code = code;
        this.description = description;
        Object.setPrototypeOf(this, BackchannelLogoutError.prototype);
    }
}
exports.BackchannelLogoutError = BackchannelLogoutError;
// eslint-disable-next-line max-len
// Basic escaping for putting untrusted data directly into the HTML body, per: https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html#rule-1-html-encode-before-inserting-untrusted-data-into-html-element-content.
function htmlSafe(input) {
    return (input &&
        input
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;'));
}
exports.htmlSafe = htmlSafe;
//# sourceMappingURL=errors.js.map