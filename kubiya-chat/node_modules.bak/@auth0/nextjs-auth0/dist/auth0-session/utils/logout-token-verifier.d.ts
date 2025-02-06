import { JWTPayload } from 'jose';
import { Config } from '../config';
import { IssuerMetadata } from '../client/abstract-client';
export type VerifyLogoutToken = (logoutToken: string, config: Config, issuerMetadata: IssuerMetadata) => Promise<JWTPayload>;
export default function getLogoutTokenVerifier(): VerifyLogoutToken;
//# sourceMappingURL=logout-token-verifier.d.ts.map