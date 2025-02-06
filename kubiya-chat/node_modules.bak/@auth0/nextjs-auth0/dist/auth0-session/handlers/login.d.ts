import { GetConfig, LoginOptions } from '../config';
import TransientStore from '../transient-store';
import { Auth0Request, Auth0Response } from '../http';
import { GetClient } from '../client/abstract-client';
export type HandleLogin = (req: Auth0Request, res: Auth0Response, options?: LoginOptions) => Promise<void>;
export type AuthVerification = {
    nonce: string;
    state: string;
    max_age?: number;
    code_verifier?: string;
    response_type?: string;
};
export default function loginHandlerFactory(getConfig: GetConfig, getClient: GetClient, transientHandler: TransientStore): HandleLogin;
//# sourceMappingURL=login.d.ts.map