import { Telemetry } from './auth0-session';
import { ConfigParameters } from './config';
import { Auth0Server } from './shared';
import { GetClient } from './auth0-session/client/abstract-client';
/**
 * Initialise your own instance of the SDK.
 *
 * See {@link ConfigParameters}.
 *
 * @category Server
 */
export type InitAuth0 = (params?: ConfigParameters) => Auth0Server;
export declare const _initAuth: ({ params, genId, clientGetter }: {
    params?: import("./auth0-session").DeepPartial<import("./config").NextConfig> | undefined;
    genId: () => string;
    clientGetter: (telemetry: Telemetry) => GetClient;
}) => Auth0Server;
//# sourceMappingURL=init.d.ts.map