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

// src/runtimes/edge/converters/index.ts
var converters_exports = {};
__export(converters_exports, {
  fromCoreMessage: () => import_fromCoreMessage.fromCoreMessage,
  fromCoreMessages: () => import_fromCoreMessage.fromCoreMessages,
  fromLanguageModelMessages: () => import_fromLanguageModelMessages.fromLanguageModelMessages,
  fromLanguageModelTools: () => import_fromLanguageModelTools.fromLanguageModelTools,
  toCoreMessage: () => import_toCoreMessages.toCoreMessage,
  toCoreMessages: () => import_toCoreMessages.toCoreMessages,
  toLanguageModelMessages: () => import_toLanguageModelMessages.toLanguageModelMessages,
  toLanguageModelTools: () => import_toLanguageModelTools.toLanguageModelTools
});
module.exports = __toCommonJS(converters_exports);
var import_toLanguageModelMessages = require("./toLanguageModelMessages.js");
var import_fromLanguageModelMessages = require("./fromLanguageModelMessages.js");
var import_fromCoreMessage = require("./fromCoreMessage.js");
var import_toCoreMessages = require("./toCoreMessages.js");
var import_fromLanguageModelTools = require("./fromLanguageModelTools.js");
var import_toLanguageModelTools = require("./toLanguageModelTools.js");
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  fromCoreMessage,
  fromCoreMessages,
  fromLanguageModelMessages,
  fromLanguageModelTools,
  toCoreMessage,
  toCoreMessages,
  toLanguageModelMessages,
  toLanguageModelTools
});
//# sourceMappingURL=index.js.map