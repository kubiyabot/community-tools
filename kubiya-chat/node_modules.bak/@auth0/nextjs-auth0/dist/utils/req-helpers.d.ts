/// <reference types="node" />
import type { IncomingMessage } from 'http';
import { NextApiRequest } from 'next';
import { NextRequest } from 'next/server';
type Req = IncomingMessage | NextApiRequest | NextRequest | Request | Record<string, any>;
export declare const isRequest: (req: Req) => boolean;
export declare const isNextApiRequest: (req: Req) => boolean;
export {};
//# sourceMappingURL=req-helpers.d.ts.map