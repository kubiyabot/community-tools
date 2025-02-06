import { CookieSerializeOptions } from 'cookie';
import { Config, GetConfig } from '../config';
import { Auth0RequestCookies, Auth0ResponseCookies } from '../http';
export interface SessionPayload<Session> {
    header: {
        /**
         * Timestamp (in secs) when the session was created.
         */
        iat: number;
        /**
         * Timestamp (in secs) when the session was last touched.
         */
        uat: number;
        /**
         * Timestamp (in secs) when the session expires.
         */
        exp: number;
    };
    /**
     * The session data.
     */
    data: Session;
}
export type Header = {
    iat: number;
    uat: number;
    exp: number;
    [propName: string]: unknown;
};
export declare abstract class AbstractSession<Session> {
    protected getConfig: (req: Auth0RequestCookies) => Config | Promise<Config>;
    constructor(getConfig: GetConfig);
    abstract getSession(req: Auth0RequestCookies): Promise<SessionPayload<Session> | undefined | null>;
    abstract setSession(req: Auth0RequestCookies, res: Auth0ResponseCookies, session: Session, uat: number, iat: number, exp: number, cookieOptions: CookieSerializeOptions, isNewSession: boolean): Promise<void>;
    abstract deleteSession(req: Auth0RequestCookies, res: Auth0ResponseCookies, cookieOptions: CookieSerializeOptions): Promise<void>;
    read(req: Auth0RequestCookies): Promise<[Session?, number?]>;
    save(req: Auth0RequestCookies, res: Auth0ResponseCookies, session: Session | null | undefined, createdAt?: number): Promise<void>;
    private calculateExp;
}
//# sourceMappingURL=abstract-session.d.ts.map