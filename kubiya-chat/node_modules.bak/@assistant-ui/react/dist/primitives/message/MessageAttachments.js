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

// src/primitives/message/MessageAttachments.tsx
var MessageAttachments_exports = {};
__export(MessageAttachments_exports, {
  MessagePrimitiveAttachments: () => MessagePrimitiveAttachments
});
module.exports = __toCommonJS(MessageAttachments_exports);
var import_react = require("react");
var import_context = require("../../context/index.js");
var import_AttachmentContext = require("../../context/react/AttachmentContext.js");
var import_AttachmentRuntimeProvider = require("../../context/providers/AttachmentRuntimeProvider.js");
var import_jsx_runtime = require("react/jsx-runtime");
var getComponent = (components, attachment) => {
  const type = attachment.type;
  switch (type) {
    case "image":
      return components?.Image ?? components?.Attachment;
    case "document":
      return components?.Document ?? components?.Attachment;
    case "file":
      return components?.File ?? components?.Attachment;
    default:
      const _exhaustiveCheck = type;
      throw new Error(`Unknown attachment type: ${_exhaustiveCheck}`);
  }
};
var AttachmentComponent = ({ components }) => {
  const Component = (0, import_AttachmentContext.useMessageAttachment)((a) => getComponent(components, a));
  if (!Component) return null;
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Component, {});
};
var MessageAttachmentImpl = ({ components, attachmentIndex }) => {
  const messageRuntime = (0, import_context.useMessageRuntime)();
  const runtime = (0, import_react.useMemo)(
    () => messageRuntime.getAttachmentByIndex(attachmentIndex),
    [messageRuntime, attachmentIndex]
  );
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(import_AttachmentRuntimeProvider.AttachmentRuntimeProvider, { runtime, children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(AttachmentComponent, { components }) });
};
var MessageAttachment = (0, import_react.memo)(
  MessageAttachmentImpl,
  (prev, next) => prev.attachmentIndex === next.attachmentIndex && prev.components?.Image === next.components?.Image && prev.components?.Document === next.components?.Document && prev.components?.File === next.components?.File && prev.components?.Attachment === next.components?.Attachment
);
var MessagePrimitiveAttachments = ({ components }) => {
  const attachmentsCount = (0, import_context.useMessage)((message) => {
    if (message.role !== "user") return 0;
    return message.attachments.length;
  });
  return Array.from({ length: attachmentsCount }, (_, index) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
    MessageAttachment,
    {
      attachmentIndex: index,
      components
    },
    index
  ));
};
MessagePrimitiveAttachments.displayName = "MessagePrimitive.Attachments";
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  MessagePrimitiveAttachments
});
//# sourceMappingURL=MessageAttachments.js.map