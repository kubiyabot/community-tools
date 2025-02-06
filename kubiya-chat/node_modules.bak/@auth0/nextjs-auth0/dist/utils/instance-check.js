"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.setIsUsingOwnInstance = exports.setIsUsingNamedExports = void 0;
let isUsingNamedExports = false;
let isUsingOwnInstance = false;
const instanceCheck = () => {
    if (isUsingNamedExports && isUsingOwnInstance) {
        throw new Error('You cannot mix creating your own instance with `initAuth0` and using named ' +
            "exports like `import { handleAuth } from '@auth0/nextjs-auth0'`");
    }
};
const setIsUsingNamedExports = () => {
    isUsingNamedExports = true;
    instanceCheck();
};
exports.setIsUsingNamedExports = setIsUsingNamedExports;
const setIsUsingOwnInstance = () => {
    isUsingOwnInstance = true;
    instanceCheck();
};
exports.setIsUsingOwnInstance = setIsUsingOwnInstance;
//# sourceMappingURL=instance-check.js.map