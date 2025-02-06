"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const session_1 = require("../session");
/**
 * @ignore
 */
function updateSessionFactory(sessionCache) {
    return async (reqOrSession, res, newSession) => {
        const session = (res ? newSession : reqOrSession);
        const req = (res ? reqOrSession : undefined);
        const [prevSession, iat] = await (0, session_1.get)({ sessionCache, req, res });
        if (!prevSession || !session || !session.user) {
            return;
        }
        await (0, session_1.set)({ req, res, session, sessionCache, iat });
    };
}
exports.default = updateSessionFactory;
//# sourceMappingURL=update-session.js.map