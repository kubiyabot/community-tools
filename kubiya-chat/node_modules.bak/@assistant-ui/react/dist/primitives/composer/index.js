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

// src/primitives/composer/index.ts
var composer_exports = {};
__export(composer_exports, {
  AddAttachment: () => import_ComposerAddAttachment.ComposerPrimitiveAddAttachment,
  Attachments: () => import_ComposerAttachments.ComposerPrimitiveAttachments,
  Cancel: () => import_ComposerCancel.ComposerPrimitiveCancel,
  If: () => import_ComposerIf.ComposerPrimitiveIf,
  Input: () => import_ComposerInput.ComposerPrimitiveInput,
  Root: () => import_ComposerRoot.ComposerPrimitiveRoot,
  Send: () => import_ComposerSend.ComposerPrimitiveSend
});
module.exports = __toCommonJS(composer_exports);
var import_ComposerRoot = require("./ComposerRoot.js");
var import_ComposerInput = require("./ComposerInput.js");
var import_ComposerSend = require("./ComposerSend.js");
var import_ComposerCancel = require("./ComposerCancel.js");
var import_ComposerAddAttachment = require("./ComposerAddAttachment.js");
var import_ComposerAttachments = require("./ComposerAttachments.js");
var import_ComposerIf = require("./ComposerIf.js");
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  AddAttachment,
  Attachments,
  Cancel,
  If,
  Input,
  Root,
  Send
});
//# sourceMappingURL=index.js.map