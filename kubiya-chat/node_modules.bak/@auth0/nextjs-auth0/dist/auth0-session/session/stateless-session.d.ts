import * as jose from 'jose';
import { CookieSerializeOptions } from 'cookie';
import { Config } from '../config';
import { AbstractSession, Header, SessionPayload } from './abstract-session';
import { Auth0RequestCookies, Auth0ResponseCookies } from '../http';
export declare class StatelessSession<Session extends {
    [key: string]: any;
} = {
    [key: string]: any;
}> extends AbstractSession<Session> {
    protected config: Config;
    private keys?;
    private chunkSize?;
    constructor(config: Config);
    private getChunkSize;
    getKeys(config: Config): Promise<Uint8Array[]>;
    encrypt(payload: jose.JWTPayload, { iat, uat, exp }: Header, key: Uint8Array): Promise<string>;
    private decrypt;
    getSession(req: Auth0RequestCookies): Promise<SessionPayload<Session> | undefined | null>;
    setSession(req: Auth0RequestCookies, res: Auth0ResponseCookies, session: Session, uat: number, iat: number, exp: number, cookieOptions: CookieSerializeOptions): Promise<void>;
    deleteSession(req: Auth0RequestCookies, res: Auth0ResponseCookies, cookieOptions: CookieSerializeOptions): Promise<void>;
}
//# sourceMappingURL=stateless-session.d.ts.map