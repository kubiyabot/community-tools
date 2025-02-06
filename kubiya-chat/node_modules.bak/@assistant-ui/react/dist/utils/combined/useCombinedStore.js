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

// src/utils/combined/useCombinedStore.ts
var useCombinedStore_exports = {};
__export(useCombinedStore_exports, {
  useCombinedStore: () => useCombinedStore
});
module.exports = __toCommonJS(useCombinedStore_exports);
var import_react = require("react");
var import_createCombinedStore = require("./createCombinedStore.js");
var useCombinedStore = (stores, selector) => {
  const useCombined = (0, import_react.useMemo)(() => (0, import_createCombinedStore.createCombinedStore)(stores), stores);
  return useCombined(selector);
};
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  useCombinedStore
});
//# sourceMappingURL=useCombinedStore.js.map