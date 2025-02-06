"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const http_1 = require("../auth0-session/http");
class Auth0NextApiResponse extends http_1.NodeResponse {
    redirect(location, status = 302) {
        if (this.res.writableEnded) {
            return;
        }
        this.res.redirect(status, this.res.getHeader('Location') || location);
    }
}
exports.default = Auth0NextApiResponse;
//# sourceMappingURL=auth0-next-api-response.js.map