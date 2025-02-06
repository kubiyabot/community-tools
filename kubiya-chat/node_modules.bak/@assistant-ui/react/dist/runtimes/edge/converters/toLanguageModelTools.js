"use strict";
var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
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
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/runtimes/edge/converters/toLanguageModelTools.ts
var toLanguageModelTools_exports = {};
__export(toLanguageModelTools_exports, {
  toLanguageModelTools: () => toLanguageModelTools
});
module.exports = __toCommonJS(toLanguageModelTools_exports);
var import_zod = require("zod");
var import_zod_to_json_schema = __toESM(require("zod-to-json-schema"));
var toLanguageModelTools = (tools) => {
  return Object.entries(tools).map(([name, tool]) => ({
    type: "function",
    name,
    ...tool.description ? { description: tool.description } : void 0,
    parameters: tool.parameters instanceof import_zod.z.ZodType ? (0, import_zod_to_json_schema.default)(tool.parameters) : tool.parameters
  }));
};
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  toLanguageModelTools
});
//# sourceMappingURL=toLanguageModelTools.js.map