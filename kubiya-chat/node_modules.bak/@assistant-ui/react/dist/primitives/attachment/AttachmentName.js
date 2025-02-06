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

// src/primitives/attachment/AttachmentName.tsx
var AttachmentName_exports = {};
__export(AttachmentName_exports, {
  AttachmentPrimitiveName: () => AttachmentPrimitiveName
});
module.exports = __toCommonJS(AttachmentName_exports);
var import_AttachmentContext = require("../../context/react/AttachmentContext.js");
var import_jsx_runtime = require("react/jsx-runtime");
var AttachmentPrimitiveName = () => {
  const name = (0, import_AttachmentContext.useAttachment)((a) => a.name);
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(import_jsx_runtime.Fragment, { children: name });
};
AttachmentPrimitiveName.displayName = "AttachmentPrimitive.Name";
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  AttachmentPrimitiveName
});
//# sourceMappingURL=AttachmentName.js.map