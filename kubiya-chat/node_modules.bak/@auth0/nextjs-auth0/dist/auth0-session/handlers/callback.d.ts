import { AuthorizationParameters, GetConfig } from '../config';
import TransientStore from '../transient-store';
import { SessionCache } from '../session-cache';
import { Auth0Request, Auth0Response } from '../http';
import { GetClient } from '../client/abstract-client';
export type AfterCallback = (session: any, state?: Record<string, any>) => Promise<any> | any | undefined;
export type CallbackOptions = {
    afterCallback?: AfterCallback;
    redirectUri?: string;
    authorizationParams?: Partial<AuthorizationParameters>;
};
export type HandleCallback = (req: Auth0Request, res: Auth0Response, options?: CallbackOptions) => Promise<void>;
export default function callbackHandlerFactory(getConfig: GetConfig, getClient: GetClient, sessionCache: SessionCache, transientCookieHandler: TransientStore): HandleCallback;
//# sourceMappingURL=callback.d.ts.map