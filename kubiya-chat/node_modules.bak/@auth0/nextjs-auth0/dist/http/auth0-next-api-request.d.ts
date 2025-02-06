import { Auth0Request } from '../auth0-session/http';
import { NextApiRequest } from 'next';
export default class Auth0NextApiRequest extends Auth0Request<NextApiRequest> {
    constructor(req: NextApiRequest);
    getUrl(): string;
    getMethod(): string;
    getBody(): Record<string, string>;
    getCookies(): Record<string, string>;
}
//# sourceMappingURL=auth0-next-api-request.d.ts.map