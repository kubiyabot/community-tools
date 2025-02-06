import * as oauth from 'oauth4webapi';
import { Auth0Request } from '../http';
import { CallbackExtras, OpenIDCallbackChecks, TokenEndpointResponse, AbstractClient, EndSessionParameters, Telemetry } from './abstract-client';
import { Config } from '../config';
export declare class EdgeClient extends AbstractClient {
    protected config: Config;
    protected telemetry: Telemetry;
    private client?;
    private as?;
    private httpOptions;
    constructor(config: Config, telemetry: Telemetry);
    private getClient;
    authorizationUrl(parameters: Record<string, unknown>): Promise<string>;
    callbackParams(req: Auth0Request, expectedState: string): Promise<URLSearchParams>;
    callback(redirectUri: string, parameters: URLSearchParams, checks: OpenIDCallbackChecks, extras: CallbackExtras): Promise<TokenEndpointResponse>;
    endSessionUrl(parameters: EndSessionParameters): Promise<string>;
    userinfo(accessToken: string): Promise<Record<string, unknown>>;
    refresh(refreshToken: string, extras: {
        exchangeBody: Record<string, any>;
    }): Promise<TokenEndpointResponse>;
    generateRandomCodeVerifier(): string;
    generateRandomNonce(): string;
    calculateCodeChallenge(codeVerifier: string): Promise<string>;
    getIssuerMetadata(): Promise<oauth.AuthorizationServer>;
}
export declare const clientGetter: (telemetry: Telemetry) => (config: Config) => Promise<EdgeClient>;
//# sourceMappingURL=edge-client.d.ts.map