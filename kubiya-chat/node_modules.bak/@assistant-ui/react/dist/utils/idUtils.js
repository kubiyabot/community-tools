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

// src/utils/idUtils.tsx
var idUtils_exports = {};
__export(idUtils_exports, {
  generateId: () => generateId,
  generateOptimisticId: () => generateOptimisticId,
  isOptimisticId: () => isOptimisticId
});
module.exports = __toCommonJS(idUtils_exports);
var import_non_secure = require("nanoid/non-secure");
var generateId = (0, import_non_secure.customAlphabet)(
  "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
  7
);
var optimisticPrefix = "__optimistic__";
var generateOptimisticId = () => `${optimisticPrefix}${generateId()}`;
var isOptimisticId = (id) => id.startsWith(optimisticPrefix);
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  generateId,
  generateOptimisticId,
  isOptimisticId
});
//# sourceMappingURL=idUtils.js.map