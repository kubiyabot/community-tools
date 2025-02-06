"use strict";
"use client";
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/primitives/thread/ThreadMessages.tsx
var ThreadMessages_exports = {};
__export(ThreadMessages_exports, {
  ThreadPrimitiveMessages: () => ThreadPrimitiveMessages,
  ThreadPrimitiveMessagesImpl: () => ThreadPrimitiveMessagesImpl
});
module.exports = __toCommonJS(ThreadMessages_exports);
var import_react = require("react");
var import_ThreadContext = require("../../context/react/ThreadContext.js");
var import_MessageRuntimeProvider = require("../../context/providers/MessageRuntimeProvider.js");
var import_context = require("../../context/index.js");
var import_jsx_runtime = require("react/jsx-runtime");
var isComponentsSame = (prev, next) => {
  return prev.Message === next.Message && prev.EditComposer === next.EditComposer && prev.UserEditComposer === next.UserEditComposer && prev.AssistantEditComposer === next.AssistantEditComposer && prev.SystemEditComposer === next.SystemEditComposer && prev.UserMessage === next.UserMessage && prev.AssistantMessage === next.AssistantMessage && prev.SystemMessage === next.SystemMessage;
};
var DEFAULT_SYSTEM_MESSAGE = () => null;
var getComponent = (components, role, isEditing) => {
  switch (role) {
    case "user":
      if (isEditing) {
        return components.UserEditComposer ?? components.EditComposer ?? components.UserMessage ?? components.Message;
      } else {
        return components.UserMessage ?? components.Message;
      }
    case "assistant":
      if (isEditing) {
        return components.AssistantEditComposer ?? components.EditComposer ?? components.AssistantMessage ?? components.Message;
      } else {
        return components.AssistantMessage ?? components.Message;
      }
    case "system":
      if (isEditing) {
        return components.SystemEditComposer ?? components.EditComposer ?? components.SystemMessage ?? components.Message;
      } else {
        return components.SystemMessage ?? DEFAULT_SYSTEM_MESSAGE;
      }
    default:
      const _exhaustiveCheck = role;
      throw new Error(`Unknown message role: ${_exhaustiveCheck}`);
  }
};
var ThreadMessageComponent = ({
  components
}) => {
  const role = (0, import_context.useMessage)((m) => m.role);
  const isEditing = (0, import_context.useEditComposer)((c) => c.isEditing);
  const Component = getComponent(components, role, isEditing);
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Component, {});
};
var ThreadMessageImpl = ({
  messageIndex,
  components
}) => {
  const threadRuntime = (0, import_ThreadContext.useThreadRuntime)();
  const runtime = (0, import_react.useMemo)(
    () => threadRuntime.getMesssageByIndex(messageIndex),
    [threadRuntime, messageIndex]
  );
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(import_MessageRuntimeProvider.MessageRuntimeProvider, { runtime, children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ThreadMessageComponent, { components }) });
};
var ThreadMessage = (0, import_react.memo)(
  ThreadMessageImpl,
  (prev, next) => prev.messageIndex === next.messageIndex && isComponentsSame(prev.components, next.components)
);
var ThreadPrimitiveMessagesImpl = ({
  components
}) => {
  const messagesLength = (0, import_ThreadContext.useThread)((t) => t.messages.length);
  if (messagesLength === 0) return null;
  return Array.from({ length: messagesLength }, (_, index) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ThreadMessage, { messageIndex: index, components }, index));
};
ThreadPrimitiveMessagesImpl.displayName = "ThreadPrimitive.Messages";
var ThreadPrimitiveMessages = (0, import_react.memo)(
  ThreadPrimitiveMessagesImpl,
  (prev, next) => isComponentsSame(prev.components, next.components)
);
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  ThreadPrimitiveMessages,
  ThreadPrimitiveMessagesImpl
});
//# sourceMappingURL=ThreadMessages.js.map