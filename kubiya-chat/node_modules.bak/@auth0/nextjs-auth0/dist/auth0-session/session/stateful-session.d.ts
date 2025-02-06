import { CookieSerializeOptions } from 'cookie';
import { AbstractSession, SessionPayload } from './abstract-session';
import { Auth0RequestCookies, Auth0ResponseCookies } from '../http';
export interface SessionStore<Session> {
    /**
     * Gets the session from the store given a session ID.
     */
    get(sid: string): Promise<SessionPayload<Session> | null | undefined>;
    /**
     * Upsert a session in the store given a session ID and `SessionData`.
     */
    set(sid: string, session: SessionPayload<Session>): Promise<void>;
    /**
     * Destroys the session with the given session ID.
     */
    delete(sid: string): Promise<void>;
}
export declare class StatefulSession<Session extends {
    [key: string]: any;
} = {
    [key: string]: any;
}> extends AbstractSession<Session> {
    private keys?;
    private store?;
    private getStore;
    private getKeys;
    getSession(req: Auth0RequestCookies): Promise<SessionPayload<Session> | undefined | null>;
    setSession(req: Auth0RequestCookies, res: Auth0ResponseCookies, session: Session, uat: number, iat: number, exp: number, cookieOptions: CookieSerializeOptions, isNewSession: boolean): Promise<void>;
    deleteSession(req: Auth0RequestCookies, res: Auth0ResponseCookies, cookieOptions: CookieSerializeOptions): Promise<void>;
}
//# sourceMappingURL=stateful-session.d.ts.map