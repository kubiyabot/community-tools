import { LanguageModelV1Message } from "@ai-sdk/provider";
import { CoreMessage } from "../../../types";
type fromLanguageModelMessagesOptions = {
    mergeSteps: boolean;
};
export declare const fromLanguageModelMessages: (lm: LanguageModelV1Message[], { mergeSteps }: fromLanguageModelMessagesOptions) => CoreMessage[];
export {};
//# sourceMappingURL=fromLanguageModelMessages.d.ts.map