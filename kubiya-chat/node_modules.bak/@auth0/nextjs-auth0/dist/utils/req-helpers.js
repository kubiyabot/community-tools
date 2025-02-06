"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.isNextApiRequest = exports.isRequest = void 0;
const isRequest = (req) => {
    return req instanceof Request || req.headers instanceof Headers || typeof req.bodyUsed === 'boolean';
};
exports.isRequest = isRequest;
const isNextApiRequest = (req) => {
    return !(0, exports.isRequest)(req) && 'query' in req;
};
exports.isNextApiRequest = isNextApiRequest;
//# sourceMappingURL=req-helpers.js.map