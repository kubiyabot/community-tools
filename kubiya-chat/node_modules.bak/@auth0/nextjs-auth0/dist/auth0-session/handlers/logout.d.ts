import { GetConfig, LogoutOptions } from '../config';
import { SessionCache } from '../session-cache';
import { Auth0Request, Auth0Response } from '../http';
import { GetClient } from '../client/abstract-client';
export type HandleLogout = (req: Auth0Request, res: Auth0Response, options?: LogoutOptions) => Promise<void>;
export default function logoutHandlerFactory(getConfig: GetConfig, getClient: GetClient, sessionCache: SessionCache): HandleLogout;
//# sourceMappingURL=logout.d.ts.map