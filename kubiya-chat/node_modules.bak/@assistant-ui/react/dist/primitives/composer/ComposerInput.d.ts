import { type TextareaAutosizeProps } from "react-textarea-autosize";
export declare namespace ComposerPrimitiveInput {
    type Element = HTMLTextAreaElement;
    type Props = TextareaAutosizeProps & {
        asChild?: boolean | undefined;
        submitOnEnter?: boolean | undefined;
        cancelOnEscape?: boolean | undefined;
        unstable_focusOnRunStart?: boolean | undefined;
        unstable_focusOnScrollToBottom?: boolean | undefined;
        unstable_focusOnThreadSwitched?: boolean | undefined;
    };
}
export declare const ComposerPrimitiveInput: import("react").ForwardRefExoticComponent<TextareaAutosizeProps & {
    asChild?: boolean | undefined;
    submitOnEnter?: boolean | undefined;
    cancelOnEscape?: boolean | undefined;
    unstable_focusOnRunStart?: boolean | undefined;
    unstable_focusOnScrollToBottom?: boolean | undefined;
    unstable_focusOnThreadSwitched?: boolean | undefined;
} & import("react").RefAttributes<HTMLTextAreaElement>>;
//# sourceMappingURL=ComposerInput.d.ts.map