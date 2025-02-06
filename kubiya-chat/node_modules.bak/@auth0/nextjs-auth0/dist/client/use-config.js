"use strict";
'use client';
Object.defineProperty(exports, "__esModule", { value: true });
exports.useConfig = void 0;
const tslib_1 = require("tslib");
const react_1 = tslib_1.__importStar(require("react"));
const Config = (0, react_1.createContext)({});
const useConfig = () => (0, react_1.useContext)(Config);
exports.useConfig = useConfig;
exports.default = ({ children, loginUrl = process.env.NEXT_PUBLIC_AUTH0_LOGIN || '/api/auth/login' }) => {
    return react_1.default.createElement(Config.Provider, { value: { loginUrl } }, children);
};
//# sourceMappingURL=use-config.js.map