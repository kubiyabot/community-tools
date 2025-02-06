import Auth0RequestCookies from './auth0-request-cookies';
export default abstract class Auth0Request<Req = any> extends Auth0RequestCookies {
    req: Req;
    protected constructor(req: Req);
    abstract getUrl(): string;
    abstract getMethod(): string;
    abstract getBody(): Promise<Record<string, string> | string> | Record<string, string> | string;
}
//# sourceMappingURL=auth0-request.d.ts.map