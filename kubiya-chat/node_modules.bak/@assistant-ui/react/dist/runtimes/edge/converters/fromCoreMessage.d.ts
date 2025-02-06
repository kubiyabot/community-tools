import { ThreadMessage, CoreMessage, MessageStatus, CompleteAttachment } from "../../../types";
export declare const fromCoreMessages: (message: readonly CoreMessage[]) => ThreadMessage[];
export declare const fromCoreMessage: (message: CoreMessage, { id, status, attachments, }?: {
    id?: string | undefined;
    status?: MessageStatus | undefined;
    attachments?: readonly CompleteAttachment[] | undefined;
}) => ThreadMessage;
//# sourceMappingURL=fromCoreMessage.d.ts.map