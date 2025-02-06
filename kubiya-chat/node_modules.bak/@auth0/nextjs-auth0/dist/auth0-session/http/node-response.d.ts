/// <reference types="node" />
import { ServerResponse } from 'http';
import { CookieSerializeOptions } from 'cookie';
import Auth0Response from './auth0-response';
export default class NodeResponse<T extends ServerResponse = ServerResponse> extends Auth0Response<ServerResponse> {
    res: T;
    constructor(res: T);
    setCookie(name: string, value: string, options?: CookieSerializeOptions): void;
    redirect(location: string, status?: number): void;
    send204(): void;
    setHeader(name: string, value: string): void;
}
//# sourceMappingURL=node-response.d.ts.map