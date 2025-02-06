"use strict";
'use client';
Object.defineProperty(exports, "__esModule", { value: true });
const tslib_1 = require("tslib");
const react_1 = tslib_1.__importStar(require("react"));
const use_config_1 = require("./use-config");
const use_user_1 = require("./use-user");
/**
 * @ignore
 */
const defaultOnRedirecting = () => react_1.default.createElement(react_1.default.Fragment, null);
/**
 * @ignore
 */
const defaultOnError = () => react_1.default.createElement(react_1.default.Fragment, null);
/**
 * @ignore
 */
const withPageAuthRequired = (Component, options = {}) => {
    return function WithPageAuthRequired(props) {
        const { returnTo, onRedirecting = defaultOnRedirecting, onError = defaultOnError } = options;
        const { loginUrl } = (0, use_config_1.useConfig)();
        const { user, error, isLoading } = (0, use_user_1.useUser)();
        (0, react_1.useEffect)(() => {
            if ((user && !error) || isLoading)
                return;
            let returnToPath;
            if (!returnTo) {
                const currentLocation = window.location.toString();
                returnToPath = currentLocation.replace(new URL(currentLocation).origin, '') || '/';
            }
            else {
                returnToPath = returnTo;
            }
            window.location.assign(`${loginUrl}?returnTo=${encodeURIComponent(returnToPath)}`);
        }, [user, error, isLoading]);
        if (error)
            return onError(error);
        if (user)
            return react_1.default.createElement(Component, Object.assign({ user: user }, props));
        return onRedirecting();
    };
};
exports.default = withPageAuthRequired;
//# sourceMappingURL=with-page-auth-required.js.map