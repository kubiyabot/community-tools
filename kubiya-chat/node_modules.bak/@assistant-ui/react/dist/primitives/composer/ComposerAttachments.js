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

// src/primitives/composer/ComposerAttachments.tsx
var ComposerAttachments_exports = {};
__export(ComposerAttachments_exports, {
  ComposerPrimitiveAttachments: () => ComposerPrimitiveAttachments
});
module.exports = __toCommonJS(ComposerAttachments_exports);
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
  const Component = (0, import_AttachmentContext.useThreadComposerAttachment)(
    (a) => getComponent(components, a)
  );
  if (!Component) return null;
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Component, {});
};
var ComposerAttachmentImpl = ({ components, attachmentIndex }) => {
  const composerRuntime = (0, import_context.useComposerRuntime)();
  const runtime = (0, import_react.useMemo)(
    () => composerRuntime.getAttachmentByIndex(attachmentIndex),
    [composerRuntime, attachmentIndex]
  );
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(import_AttachmentRuntimeProvider.AttachmentRuntimeProvider, { runtime, children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(AttachmentComponent, { components }) });
};
var ComposerAttachment = (0, import_react.memo)(
  ComposerAttachmentImpl,
  (prev, next) => prev.attachmentIndex === next.attachmentIndex && prev.components?.Image === next.components?.Image && prev.components?.Document === next.components?.Document && prev.components?.File === next.components?.File && prev.components?.Attachment === next.components?.Attachment
);
var ComposerPrimitiveAttachments = ({ components }) => {
  const attachmentsCount = (0, import_context.useComposer)((s) => s.attachments.length);
  return Array.from({ length: attachmentsCount }, (_, index) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
    ComposerAttachment,
    {
      attachmentIndex: index,
      components
    },
    index
  ));
};
ComposerPrimitiveAttachments.displayName = "ComposerPrimitive.Attachments";
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  ComposerPrimitiveAttachments
});
//# sourceMappingURL=ComposerAttachments.js.map