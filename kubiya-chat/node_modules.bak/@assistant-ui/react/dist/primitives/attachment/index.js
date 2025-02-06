"use strict";
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

// src/primitives/attachment/index.ts
var attachment_exports = {};
__export(attachment_exports, {
  Name: () => import_AttachmentName.AttachmentPrimitiveName,
  Remove: () => import_AttachmentRemove.AttachmentPrimitiveRemove,
  Root: () => import_AttachmentRoot.AttachmentPrimitiveRoot,
  unstable_Thumb: () => import_AttachmentThumb.AttachmentPrimitiveThumb
});
module.exports = __toCommonJS(attachment_exports);
var import_AttachmentRoot = require("./AttachmentRoot.js");
var import_AttachmentThumb = require("./AttachmentThumb.js");
var import_AttachmentName = require("./AttachmentName.js");
var import_AttachmentRemove = require("./AttachmentRemove.js");
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  Name,
  Remove,
  Root,
  unstable_Thumb
});
//# sourceMappingURL=index.js.map