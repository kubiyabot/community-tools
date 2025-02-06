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

// src/primitives/message/index.ts
var message_exports = {};
__export(message_exports, {
  Attachments: () => import_MessageAttachments.MessagePrimitiveAttachments,
  Content: () => import_MessageContent.MessagePrimitiveContent,
  If: () => import_MessageIf.MessagePrimitiveIf,
  Root: () => import_MessageRoot.MessagePrimitiveRoot
});
module.exports = __toCommonJS(message_exports);
var import_MessageRoot = require("./MessageRoot.js");
var import_MessageIf = require("./MessageIf.js");
var import_MessageContent = require("./MessageContent.js");
var import_MessageAttachments = require("./MessageAttachments.js");
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  Attachments,
  Content,
  If,
  Root
});
//# sourceMappingURL=index.js.map