import { Auth0Request, Auth0Response } from '../http';
import { Config, GetConfig } from '../config';
import { GetClient } from '../client/abstract-client';
export type HandleBackchannelLogout = (req: Auth0Request, res: Auth0Response) => Promise<void>;
export default function backchannelLogoutHandlerFactory(getConfig: GetConfig, getClient: GetClient): HandleBackchannelLogout;
export type IsLoggedOut = (user: {
    [key: string]: any;
}, config: Config) => Promise<boolean>;
export declare const isLoggedOut: IsLoggedOut;
export type DeleteSub = (sub: string, config: Config) => Promise<void>;
export declare const deleteSub: DeleteSub;
//# sourceMappingURL=backchannel-logout.d.ts.map