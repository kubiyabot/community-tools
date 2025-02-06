"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.get = void 0;
const tslib_1 = require("tslib");
const joi_1 = tslib_1.__importDefault(require("joi"));
const get_login_state_1 = require("./hooks/get-login-state");
const isHttps = /^https:/i;
const paramsSchema = joi_1.default.object({
    secret: joi_1.default.alternatives([joi_1.default.string().min(8), joi_1.default.array().items(joi_1.default.string().min(8))]).required(),
    session: joi_1.default.object({
        rolling: joi_1.default.boolean().optional().default(true),
        rollingDuration: joi_1.default.when(joi_1.default.ref('rolling'), {
            is: true,
            then: joi_1.default.number().integer().messages({
                'number.base': '"session.rollingDuration" must be provided an integer value when "session.rolling" is true'
            }),
            otherwise: joi_1.default.boolean().valid(false).messages({
                'any.only': '"session.rollingDuration" must be false when "session.rolling" is disabled'
            })
        })
            .optional()
            .default((parent) => (parent.rolling ? 24 * 60 * 60 : false)),
        absoluteDuration: joi_1.default.when(joi_1.default.ref('rolling'), {
            is: false,
            then: joi_1.default.number().integer().messages({
                'number.base': '"session.absoluteDuration" must be provided an integer value when "session.rolling" is false'
            }),
            otherwise: joi_1.default.alternatives([joi_1.default.number().integer(), joi_1.default.boolean().valid(false)])
        })
            .optional()
            .default(7 * 24 * 60 * 60),
        autoSave: joi_1.default.boolean().optional().default(true),
        name: joi_1.default.string().token().optional().default('appSession'),
        store: joi_1.default.object()
            .optional()
            .when(joi_1.default.ref('/backchannelLogout'), {
            not: false,
            then: joi_1.default.when('/backchannelLogout.store', {
                not: joi_1.default.exist(),
                then: joi_1.default.object().required().messages({
                    // eslint-disable-next-line max-len
                    'any.required': `Back-Channel Logout requires a "backchannelLogout.store" (you can also reuse "session.store" if you have stateful sessions).`
                })
            })
        }),
        genId: joi_1.default.function().maxArity(2).when(joi_1.default.ref('store'), { then: joi_1.default.required() }),
        storeIDToken: joi_1.default.boolean().optional().default(true),
        cookie: joi_1.default.object({
            domain: joi_1.default.string().optional(),
            transient: joi_1.default.boolean().optional().default(false),
            httpOnly: joi_1.default.boolean().optional().default(true),
            sameSite: joi_1.default.string().valid('lax', 'strict', 'none').optional().default('lax'),
            secure: joi_1.default.when(joi_1.default.ref('/baseURL'), {
                is: joi_1.default.string().pattern(isHttps),
                then: joi_1.default.boolean().valid(true).default(true).messages({
                    'any.only': 'Cookies must be secure when base url is https.'
                }),
                otherwise: joi_1.default.boolean().valid(false).default(false).messages({
                    'any.only': 'Cookies set with the `Secure` property wont be attached to http requests'
                })
            }),
            path: joi_1.default.string().uri({ relativeOnly: true }).optional()
        })
            .default()
            .unknown(false)
    })
        .default()
        .unknown(false),
    auth0Logout: joi_1.default.boolean().optional(),
    authorizationParams: joi_1.default.object({
        response_type: joi_1.default.string().optional().valid('id_token', 'code id_token', 'code').default('id_token'),
        scope: joi_1.default.string()
            .optional()
            .pattern(/\bopenid\b/, 'contains openid')
            .default('openid profile email'),
        response_mode: joi_1.default.string()
            .optional()
            .when('response_type', {
            is: 'code',
            then: joi_1.default.valid('query', 'form_post'),
            otherwise: joi_1.default.valid('form_post').default('form_post')
        })
    })
        .optional()
        .unknown(true)
        .default(),
    baseURL: joi_1.default.string()
        .uri()
        .required()
        .when(joi_1.default.ref('authorizationParams.response_mode'), {
        is: 'form_post',
        then: joi_1.default.string()
            .pattern(isHttps)
            .rule({
            warn: true,
            message: "Using 'form_post' for response_mode may cause issues for you logging in over http, " +
                'see https://github.com/auth0/express-openid-connect/blob/master/FAQ.md'
        })
    }),
    clientID: joi_1.default.string().required(),
    clientSecret: joi_1.default.string()
        .when(joi_1.default.ref('clientAuthMethod', {
        adjust: (value) => value && value.includes('client_secret')
    }), {
        is: true,
        then: joi_1.default.string().required().messages({
            'any.required': '"clientSecret" is required for the clientAuthMethod {{clientAuthMethod}}'
        })
    })
        .when(joi_1.default.ref('idTokenSigningAlg', {
        adjust: (value) => value && value.startsWith('HS')
    }), {
        is: true,
        then: joi_1.default.string().required().messages({
            'any.required': '"clientSecret" is required for ID tokens with HMAC based algorithms'
        })
    }),
    clockTolerance: joi_1.default.number().optional().default(60),
    httpTimeout: joi_1.default.number().optional().default(5000),
    httpAgent: joi_1.default.object().optional(),
    enableTelemetry: joi_1.default.boolean().optional().default(true),
    getLoginState: joi_1.default.function()
        .optional()
        .default(() => get_login_state_1.getLoginState),
    identityClaimFilter: joi_1.default.array()
        .optional()
        .default(['aud', 'iss', 'iat', 'exp', 'nbf', 'nonce', 'azp', 'auth_time', 's_hash', 'at_hash', 'c_hash']),
    idpLogout: joi_1.default.boolean()
        .optional()
        .default((parent) => parent.auth0Logout || false),
    idTokenSigningAlg: joi_1.default.string().insensitive().not('none').optional().default('RS256'),
    issuerBaseURL: joi_1.default.string().uri().required(),
    legacySameSiteCookie: joi_1.default.boolean().optional().default(true),
    routes: joi_1.default.object({
        callback: joi_1.default.string().uri({ relativeOnly: true }).required(),
        postLogoutRedirect: joi_1.default.string().uri({ allowRelative: true }).default('')
    })
        .default()
        .unknown(false),
    clientAuthMethod: joi_1.default.string()
        .valid('client_secret_basic', 'client_secret_post', 'client_secret_jwt', 'private_key_jwt', 'none')
        .optional()
        .default((parent) => {
        if (parent.authorizationParams.response_type === 'id_token' && !parent.pushedAuthorizationRequests) {
            return 'none';
        }
        if (parent.clientAssertionSigningKey) {
            return 'private_key_jwt';
        }
        return 'client_secret_basic';
    })
        .when(joi_1.default.ref('authorizationParams.response_type', {
        adjust: (value) => value && value.includes('code')
    }), {
        is: true,
        then: joi_1.default.string().invalid('none').messages({
            'any.only': 'Public code flow clients are not supported.'
        })
    })
        .when(joi_1.default.ref('pushedAuthorizationRequests'), {
        is: true,
        then: joi_1.default.string().invalid('none').messages({
            'any.only': 'Public PAR clients are not supported'
        })
    }),
    clientAssertionSigningKey: joi_1.default.any()
        .optional()
        .when(joi_1.default.ref('clientAuthMethod'), {
        is: 'private_key_jwt',
        then: joi_1.default.any().required().messages({
            'any.required': '"clientAssertionSigningKey" is required for a "clientAuthMethod" of "private_key_jwt"'
        })
    }),
    clientAssertionSigningAlg: joi_1.default.string()
        .optional()
        .valid('RS256', 'RS384', 'RS512', 'PS256', 'PS384', 'PS512', 'ES256', 'ES256K', 'ES384', 'ES512', 'EdDSA'),
    transactionCookie: joi_1.default.object({
        name: joi_1.default.string().default('auth_verification'),
        domain: joi_1.default.string().default(joi_1.default.ref('/session.cookie.domain')),
        secure: joi_1.default.boolean().default(joi_1.default.ref('/session.cookie.secure')),
        sameSite: joi_1.default.string().valid('lax', 'strict', 'none').default(joi_1.default.ref('/session.cookie.sameSite')),
        path: joi_1.default.string().uri({ relativeOnly: true }).default(joi_1.default.ref('/session.cookie.transient'))
    })
        .default()
        .unknown(false),
    backchannelLogout: joi_1.default.alternatives([
        joi_1.default.object({
            store: joi_1.default.object().optional()
        }),
        joi_1.default.boolean()
    ]).default(false),
    pushedAuthorizationRequests: joi_1.default.boolean().optional().default(false)
});
const get = (params = {}) => {
    const { value, error, warning } = paramsSchema.validate(params, { allowUnknown: true });
    if (error) {
        throw new TypeError(error.details[0].message);
    }
    if (warning) {
        console.warn(warning.message);
    }
    return value;
};
exports.get = get;
//# sourceMappingURL=get-config.js.map