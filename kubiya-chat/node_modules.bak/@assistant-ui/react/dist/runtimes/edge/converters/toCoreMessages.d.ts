import { ThreadMessage, CoreMessage } from "../../../types";
type CoreMessageWithConditionalId<T extends boolean> = T extends false ? CoreMessage : CoreMessage & {
    unstable_id?: string;
};
export declare const toCoreMessages: <T extends boolean = false>(messages: readonly ThreadMessage[], options?: {
    unstable_includeId?: T | undefined;
}) => CoreMessageWithConditionalId<T>[];
export declare const toCoreMessage: <T extends boolean = false>(message: ThreadMessage, options?: {
    unstable_includeId?: T | undefined;
}) => CoreMessageWithConditionalId<T>;
export {};
//# sourceMappingURL=toCoreMessages.d.ts.map