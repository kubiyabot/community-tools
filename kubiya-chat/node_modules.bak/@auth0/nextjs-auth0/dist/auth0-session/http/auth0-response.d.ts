import Auth0ResponseCookies from './auth0-response-cookies';
export default abstract class Auth0Response<Res = any> extends Auth0ResponseCookies {
    res: Res;
    protected constructor(res: Res);
    abstract redirect(location: string, status?: number): void;
    abstract send204(): void;
    abstract setHeader(name: string, value: string): void;
}
//# sourceMappingURL=auth0-response.d.ts.map