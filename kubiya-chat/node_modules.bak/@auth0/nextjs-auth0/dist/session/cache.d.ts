/// <reference types="node" />
import { IncomingMessage, ServerResponse } from 'http';
import { NextApiRequest, NextApiResponse } from 'next';
import { NextRequest, NextResponse } from 'next/server';
import type { TokenEndpointResponse } from '../auth0-session';
import { SessionCache as ISessionCache, AbstractSession } from '../auth0-session';
import Session from './session';
import { Auth0Request, Auth0Response } from '../auth0-session/http';
import { GetConfig, NextConfig } from '../config';
type Req = IncomingMessage | NextRequest | NextApiRequest;
type Res = ServerResponse | NextResponse | NextApiResponse;
export declare const getAuth0ReqRes: (req: Req, res: Res) => [Auth0Request, Auth0Response];
export default class SessionCache implements ISessionCache<Req, Res, Session> {
    getConfig: GetConfig;
    private cache;
    private iatCache;
    private sessionStore?;
    constructor(getConfig: GetConfig);
    getSessionStore(config: NextConfig): AbstractSession<Session>;
    private init;
    save(req: Req, res: Res): Promise<void>;
    create(req: Req, res: Res, session: Session): Promise<void>;
    delete(req: Req, res: Res): Promise<void>;
    isAuthenticated(req: Req, res: Res): Promise<boolean>;
    getIdToken(req: Req, res: Res): Promise<string | undefined>;
    set(req: Req, res: Res, session: Session | null | undefined): Promise<void>;
    get(req: Req, res: Res): Promise<Session | null | undefined>;
    fromTokenEndpointResponse(req: Req, res: Res, tokenSet: TokenEndpointResponse): Promise<Session>;
}
export declare const get: ({ sessionCache, req, res }: {
    sessionCache: SessionCache;
    req?: Req | undefined;
    res?: Res | undefined;
}) => Promise<[(Session | null)?, number?]>;
export declare const set: ({ session, sessionCache, iat, req, res }: {
    session?: Session | null | undefined;
    sessionCache: SessionCache;
    iat?: number | undefined;
    req?: Req | undefined;
    res?: Res | undefined;
}) => Promise<void>;
export {};
//# sourceMappingURL=cache.d.ts.map