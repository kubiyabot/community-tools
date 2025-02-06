import { HandleBackchannelLogout as BaseHandleBackchannelLogout } from '../auth0-session';
import { Handler } from './router-helpers';
import { GetConfig } from '../config';
/**
 * The handler for the POST `/api/auth/backchannel-logout` API route.
 *
 * @category Server
 */
export type HandleBackchannelLogout = Handler;
/**
 * @ignore
 */
export default function handleBackchannelLogoutFactory(handler: BaseHandleBackchannelLogout, getConfig: GetConfig): HandleBackchannelLogout;
//# sourceMappingURL=backchannel-logout.d.ts.map