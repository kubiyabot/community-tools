/// <reference types="node" />
import { IncomingMessage } from 'http';
import Auth0Request from './auth0-request';
export default class NodeRequest extends Auth0Request<IncomingMessage> {
    req: IncomingMessage;
    constructor(req: IncomingMessage);
    getUrl(): string;
    getMethod(): string;
    getBody(): Record<string, string>;
    getCookies(): Record<string, string>;
}
//# sourceMappingURL=node-request.d.ts.map