import { Auth0Request } from '../http';
import { CallbackExtras, OpenIDCallbackChecks, TokenEndpointResponse, AbstractClient, Telemetry } from './abstract-client';
import { EndSessionParameters, IssuerMetadata } from 'openid-client';
import { Config } from '../config';
export declare class NodeClient extends AbstractClient {
    private client?;
    private getClient;
    authorizationUrl(parameters: Record<string, unknown>): Promise<string>;
    callbackParams(req: Auth0Request): Promise<URLSearchParams>;
    callback(redirectUri: string, parameters: URLSearchParams, checks: OpenIDCallbackChecks, extras: CallbackExtras): Promise<TokenEndpointResponse>;
    endSessionUrl(parameters: EndSessionParameters): Promise<string>;
    userinfo(accessToken: string): Promise<Record<string, unknown>>;
    refresh(refreshToken: string, extras: {
        exchangeBody: Record<string, any>;
    }): Promise<TokenEndpointResponse>;
    generateRandomCodeVerifier(): string;
    generateRandomNonce(): string;
    calculateCodeChallenge(codeVerifier: string): string;
    getIssuerMetadata(): Promise<IssuerMetadata>;
}
export declare const clientGetter: (telemetry: Telemetry) => (config: Config) => Promise<NodeClient>;
//# sourceMappingURL=node-client.d.ts.map