import { NextResponse } from 'next/server';
import type { CookieSerializeOptions } from 'cookie';
import { Auth0Response } from '../auth0-session/http';
export default class Auth0NextResponse extends Auth0Response<NextResponse> {
    constructor(res: NextResponse);
    setCookie(name: string, value: string, options?: CookieSerializeOptions): void;
    clearCookie(name: string, options?: CookieSerializeOptions): void;
    redirect(location: string, status?: number): void;
    setHeader(name: string, value: string): void;
    send204(): void;
}
//# sourceMappingURL=auth0-next-response.d.ts.map