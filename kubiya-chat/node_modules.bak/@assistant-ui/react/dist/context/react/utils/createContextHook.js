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

// src/context/react/utils/createContextHook.ts
var createContextHook_exports = {};
__export(createContextHook_exports, {
  createContextHook: () => createContextHook
});
module.exports = __toCommonJS(createContextHook_exports);
var import_react = require("react");
function createContextHook(context, providerName) {
  function useContextHook(options) {
    const contextValue = (0, import_react.useContext)(context);
    if (!options?.optional && !contextValue) {
      throw new Error(`This component must be used within ${providerName}.`);
    }
    return contextValue;
  }
  return useContextHook;
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  createContextHook
});
//# sourceMappingURL=createContextHook.js.map