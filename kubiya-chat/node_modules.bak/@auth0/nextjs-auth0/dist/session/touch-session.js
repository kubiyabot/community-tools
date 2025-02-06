"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const session_1 = require("../session");
/**
 * @ignore
 */
function touchSessionFactory(sessionCache) {
    return async (req, res) => {
        const [session, iat] = await (0, session_1.get)({ sessionCache, req, res });
        if (!session) {
            return;
        }
        await (0, session_1.set)({ req, res, session, sessionCache, iat });
    };
}
exports.default = touchSessionFactory;
//# sourceMappingURL=touch-session.js.map