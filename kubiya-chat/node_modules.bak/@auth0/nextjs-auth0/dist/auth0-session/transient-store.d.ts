import { Config, GetConfig } from './config';
import { Auth0Request, Auth0RequestCookies, Auth0Response } from './http';
export interface StoreOptions {
    sameSite?: boolean | 'lax' | 'strict' | 'none';
    value: string;
}
export default class TransientStore {
    private keys?;
    protected getConfig: (req: Auth0RequestCookies) => Config | Promise<Config>;
    constructor(getConfig: GetConfig);
    private getKeys;
    /**
     * Set a cookie with a value or a generated nonce.
     *
     * @param {String} key Cookie name to use.
     * @param {IncomingMessage} req Server Request object.
     * @param {ServerResponse} res Server Response object.
     * @param {Object} opts Options object.
     * @param {String} opts.sameSite SameSite attribute of `None`, `Lax`, or `Strict`. Defaults to `None`.
     * @param {String} opts.value Cookie value. Omit this key to store a generated value.
     *
     * @return {String} Cookie value that was set.
     */
    save(key: string, req: Auth0Request, res: Auth0Response, { sameSite, value }: StoreOptions): Promise<string>;
    /**
     * Get a cookie value then delete it.
     *
     * @param {String} key Cookie name to use.
     * @param {IncomingMessage} req Express Request object.
     * @param {ServerResponse} res Express Response object.
     *
     * @return {String|undefined} Cookie value or undefined if cookie was not found.
     */
    read(key: string, req: Auth0Request, res: Auth0Response): Promise<string | undefined>;
}
//# sourceMappingURL=transient-store.d.ts.map