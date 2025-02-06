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

// src/primitives/assistantModal/index.ts
var assistantModal_exports = {};
__export(assistantModal_exports, {
  Anchor: () => import_AssistantModalAnchor.AssistantModalPrimitiveAnchor,
  Content: () => import_AssistantModalContent.AssistantModalPrimitiveContent,
  Root: () => import_AssistantModalRoot.AssistantModalPrimitiveRoot,
  Trigger: () => import_AssistantModalTrigger.AssistantModalPrimitiveTrigger
});
module.exports = __toCommonJS(assistantModal_exports);
var import_AssistantModalRoot = require("./AssistantModalRoot.js");
var import_AssistantModalTrigger = require("./AssistantModalTrigger.js");
var import_AssistantModalContent = require("./AssistantModalContent.js");
var import_AssistantModalAnchor = require("./AssistantModalAnchor.js");
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  Anchor,
  Content,
  Root,
  Trigger
});
//# sourceMappingURL=index.js.map