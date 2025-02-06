import { MessageStatus } from "../../types";
export declare const isAutoStatus: (status: MessageStatus) => boolean;
export declare const getAutoStatus: (isLast: boolean, isRunning: boolean) => Readonly<{
    type: "running";
}> | Readonly<{
    type: "complete";
    reason: "unknown";
}>;
//# sourceMappingURL=auto-status.d.ts.map