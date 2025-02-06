"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.handleAuth = exports.handleProfile = exports.handleCallback = exports.handleLogout = exports.handleLogin = exports.withPageAuthRequired = exports.withApiAuthRequired = exports.touchSession = exports.getAccessToken = exports.updateSession = exports.getSession = exports.initAuth0 = void 0;
const tslib_1 = require("tslib");
const crypto_1 = tslib_1.__importDefault(require("crypto"));
const init_1 = require("./init");
const instance_check_1 = require("./utils/instance-check");
const node_client_1 = require("./auth0-session/client/node-client");
const genId = () => crypto_1.default.randomBytes(16).toString('hex');
let instance;
// For using managed instance with named exports.
function getInstance() {
    (0, instance_check_1.setIsUsingNamedExports)();
    if (instance) {
        return instance;
    }
    instance = (0, init_1._initAuth)({ genId, clientGetter: node_client_1.clientGetter });
    return instance;
}
// For creating own instance.
const initAuth0 = (params) => {
    (0, instance_check_1.setIsUsingOwnInstance)();
    const _a = (0, init_1._initAuth)({
        genId,
        params,
        clientGetter: node_client_1.clientGetter
    }), { withMiddlewareAuthRequired } = _a, publicApi = tslib_1.__rest(_a, ["withMiddlewareAuthRequired"]);
    return publicApi;
};
exports.initAuth0 = initAuth0;
const getSession = (...args) => getInstance().getSession(...args);
exports.getSession = getSession;
const updateSession = (...args) => getInstance().updateSession(...args);
exports.updateSession = updateSession;
const getAccessToken = (...args) => getInstance().getAccessToken(...args);
exports.getAccessToken = getAccessToken;
const touchSession = (...args) => getInstance().touchSession(...args);
exports.touchSession = touchSession;
const withApiAuthRequired = (...args) => getInstance().withApiAuthRequired(...args);
exports.withApiAuthRequired = withApiAuthRequired;
exports.withPageAuthRequired = ((...args) => getInstance().withPageAuthRequired(...args));
exports.handleLogin = ((...args) => getInstance().handleLogin(...args));
exports.handleLogout = ((...args) => getInstance().handleLogout(...args));
exports.handleCallback = ((...args) => getInstance().handleCallback(...args));
exports.handleProfile = ((...args) => getInstance().handleProfile(...args));
const handleAuth = (...args) => getInstance().handleAuth(...args);
exports.handleAuth = handleAuth;
tslib_1.__exportStar(require("./shared"), exports);
//# sourceMappingURL=index.js.map