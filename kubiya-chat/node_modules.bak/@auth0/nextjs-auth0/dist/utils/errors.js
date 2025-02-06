"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ProfileHandlerError = exports.LogoutHandlerError = exports.LoginHandlerError = exports.CallbackHandlerError = exports.HandlerError = exports.AccessTokenError = exports.AccessTokenErrorCode = exports.AuthError = exports.appendCause = void 0;
/**
 * @ignore
 */
function appendCause(errorMessage, cause) {
    if (!cause)
        return errorMessage;
    const separator = errorMessage.endsWith('.') ? '' : '.';
    return `${errorMessage}${separator} CAUSE: ${cause.message}`;
}
exports.appendCause = appendCause;
/**
 * The base class for all SDK errors.
 *
 * Because part of the error message can come from the OpenID Connect `error` query parameter we
 * do some basic escaping which makes sure the default error handler is safe from XSS.
 *
 * **IMPORTANT** If you write your own error handler, you should **not** render the error
 * without using a templating engine that will properly escape it for other HTML contexts first.
 *
 * Note that the error message of the {@link AuthError.cause | underlying error} is **not** escaped
 * in any way, so do **not** render it without escaping it first!
 *
 * @category Server
 */
class AuthError extends Error {
    constructor(options) {
        /* c8 ignore next */
        super(appendCause(options.message, options.cause));
        this.code = options.code;
        this.name = options.name;
        this.cause = options.cause;
        this.status = options.status;
    }
}
exports.AuthError = AuthError;
/**
 * Error codes for {@link AccessTokenError}.
 *
 * @category Server
 */
var AccessTokenErrorCode;
(function (AccessTokenErrorCode) {
    AccessTokenErrorCode["MISSING_SESSION"] = "ERR_MISSING_SESSION";
    AccessTokenErrorCode["MISSING_ACCESS_TOKEN"] = "ERR_MISSING_ACCESS_TOKEN";
    AccessTokenErrorCode["MISSING_REFRESH_TOKEN"] = "ERR_MISSING_REFRESH_TOKEN";
    AccessTokenErrorCode["EXPIRED_ACCESS_TOKEN"] = "ERR_EXPIRED_ACCESS_TOKEN";
    AccessTokenErrorCode["INSUFFICIENT_SCOPE"] = "ERR_INSUFFICIENT_SCOPE";
    AccessTokenErrorCode["FAILED_REFRESH_GRANT"] = "ERR_FAILED_REFRESH_GRANT";
})(AccessTokenErrorCode = exports.AccessTokenErrorCode || (exports.AccessTokenErrorCode = {}));
/**
 * The error thrown by {@link GetAccessToken}.
 *
 * @see the {@link AuthError.code | code property} contains a machine-readable error code that
 * remains stable within a major version of the SDK. You should rely on this error code to handle
 * errors. In contrast, the error message is not part of the API and can change anytime. Do **not**
 * parse or otherwise rely on the error message to handle errors.
 *
 * @see {@link AccessTokenErrorCode} for the list of all possible error codes.
 * @category Server
 */
class AccessTokenError extends AuthError {
    constructor(code, message, cause) {
        /* c8 ignore next */
        super({ code: code, message: message, name: 'AccessTokenError', cause });
        // Capturing stack trace, excluding constructor call from it.
        Error.captureStackTrace(this, this.constructor);
        Object.setPrototypeOf(this, AccessTokenError.prototype);
    }
}
exports.AccessTokenError = AccessTokenError;
/**
 * The base class for errors thrown by API route handlers. It extends {@link AuthError}.
 *
 * Because part of the error message can come from the OpenID Connect `error` query parameter we
 * do some basic escaping which makes sure the default error handler is safe from XSS.
 *
 * **IMPORTANT** If you write your own error handler, you should **not** render the error message
 * without using a templating engine that will properly escape it for other HTML contexts first.
 *
 * @see the {@link AuthError.cause | cause property} contains the underlying error.
 * **IMPORTANT** When this error is from the Identity Provider ({@link IdentityProviderError}) it can contain user
 * input and is only escaped using basic escaping for putting untrusted data directly into the HTML body.
 * You should **not** render this error without using a templating engine that will properly escape it for other
 * HTML contexts first.
 *
 * @see the {@link AuthError.status | status property} contains the HTTP status code of the error,
 * if any.
 *
 * @category Server
 */
class HandlerError extends AuthError {
    constructor(options) {
        let status;
        if ('status' in options.cause)
            status = options.cause.status;
        /* c8 ignore next */
        super(Object.assign(Object.assign({}, options), { status }));
    }
}
exports.HandlerError = HandlerError;
/**
 * The error thrown by the callback API route handler. It extends {@link HandlerError}.
 *
 * Because part of the error message can come from the OpenID Connect `error` query parameter we
 * do some basic escaping which makes sure the default error handler is safe from XSS.
 *
 * **IMPORTANT** If you write your own error handler, you should **not** render the error message
 * without using a templating engine that will properly escape it for other HTML contexts first.
 *
 * @see the {@link AuthError.cause | cause property} contains the underlying error.
 * **IMPORTANT** When this error is from the Identity Provider ({@link IdentityProviderError}) it can contain user
 * input and is only escaped using basic escaping for putting untrusted data directly into the HTML body.
 * You should **not** render this error without using a templating engine that will properly escape it for other
 * HTML contexts first.
 *
 * @see the {@link AuthError.status | status property} contains the HTTP status code of the error,
 * if any.
 *
 * @category Server
 */
class CallbackHandlerError extends HandlerError {
    constructor(cause) {
        super({
            code: CallbackHandlerError.code,
            message: 'Callback handler failed.',
            name: 'CallbackHandlerError',
            cause
        }); /* c8 ignore next */
        Object.setPrototypeOf(this, CallbackHandlerError.prototype);
    }
}
exports.CallbackHandlerError = CallbackHandlerError;
CallbackHandlerError.code = 'ERR_CALLBACK_HANDLER_FAILURE';
/**
 * The error thrown by the login API route handler. It extends {@link HandlerError}.
 *
 * @see the {@link AuthError.cause | cause property} contains the underlying error.
 * @category Server
 */
class LoginHandlerError extends HandlerError {
    constructor(cause) {
        super({
            code: LoginHandlerError.code,
            message: 'Login handler failed.',
            name: 'LoginHandlerError',
            cause
        }); /* c8 ignore next */
        Object.setPrototypeOf(this, LoginHandlerError.prototype);
    }
}
exports.LoginHandlerError = LoginHandlerError;
LoginHandlerError.code = 'ERR_LOGIN_HANDLER_FAILURE';
/**
 * The error thrown by the logout API route handler. It extends {@link HandlerError}.
 *
 * @see the {@link AuthError.cause | cause property} contains the underlying error.
 * @category Server
 */
class LogoutHandlerError extends HandlerError {
    constructor(cause) {
        super({
            code: LogoutHandlerError.code,
            message: 'Logout handler failed.',
            name: 'LogoutHandlerError',
            cause
        }); /* c8 ignore next */
        Object.setPrototypeOf(this, LogoutHandlerError.prototype);
    }
}
exports.LogoutHandlerError = LogoutHandlerError;
LogoutHandlerError.code = 'ERR_LOGOUT_HANDLER_FAILURE';
/**
 * The error thrown by the profile API route handler. It extends {@link HandlerError}.
 *
 * @see the {@link AuthError.cause | cause property} contains the underlying error.
 * @category Server
 */
class ProfileHandlerError extends HandlerError {
    constructor(cause) {
        super({
            code: ProfileHandlerError.code,
            message: 'Profile handler failed.',
            name: 'ProfileHandlerError',
            cause
        }); /* c8 ignore next */
        Object.setPrototypeOf(this, ProfileHandlerError.prototype);
    }
}
exports.ProfileHandlerError = ProfileHandlerError;
ProfileHandlerError.code = 'ERR_PROFILE_HANDLER_FAILURE';
//# sourceMappingURL=errors.js.map