import { Auth0Request } from '../auth0-session/http';
import { NextRequest } from 'next/server';
export default class Auth0NextRequest extends Auth0Request<NextRequest> {
    constructor(req: NextRequest);
    getUrl(): string;
    getMethod(): string;
    getBody(): Promise<Record<string, string> | string>;
    getCookies(): Record<string, string>;
}
//# sourceMappingURL=auth0-next-request.d.ts.map