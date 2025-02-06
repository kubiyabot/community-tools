"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const session_1 = require("../session");
/**
 * @ignore
 */
function sessionFactory(sessionCache) {
    return async (req, res) => {
        const [session] = await (0, session_1.get)({ req, res, sessionCache });
        return session;
    };
}
exports.default = sessionFactory;
//# sourceMappingURL=get-session.js.map