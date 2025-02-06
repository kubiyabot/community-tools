import { type ComponentType, type FC } from "react";
export declare namespace ThreadPrimitiveMessages {
    type Props = {
        components: {
            Message: ComponentType;
            EditComposer?: ComponentType | undefined;
            UserEditComposer?: ComponentType | undefined;
            AssistantEditComposer?: ComponentType | undefined;
            SystemEditComposer?: ComponentType | undefined;
            UserMessage?: ComponentType | undefined;
            AssistantMessage?: ComponentType | undefined;
            SystemMessage?: ComponentType | undefined;
        } | {
            Message?: ComponentType | undefined;
            EditComposer?: ComponentType | undefined;
            UserEditComposer?: ComponentType | undefined;
            AssistantEditComposer?: ComponentType | undefined;
            SystemEditComposer?: ComponentType | undefined;
            UserMessage: ComponentType;
            AssistantMessage: ComponentType;
            SystemMessage?: ComponentType | undefined;
        };
    };
}
export declare const ThreadPrimitiveMessagesImpl: FC<ThreadPrimitiveMessages.Props>;
export declare const ThreadPrimitiveMessages: import("react").NamedExoticComponent<ThreadPrimitiveMessages.Props>;
//# sourceMappingURL=ThreadMessages.d.ts.map