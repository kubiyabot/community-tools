import { NodeResponse } from '../auth0-session/http';
import { NextApiResponse } from 'next';
export default class Auth0NextApiResponse extends NodeResponse<NextApiResponse> {
    redirect(location: string, status?: number): void;
}
//# sourceMappingURL=auth0-next-api-response.d.ts.map