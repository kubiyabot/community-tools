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

// src/context/react/utils/createContextStoreHook.ts
var createContextStoreHook_exports = {};
__export(createContextStoreHook_exports, {
  createContextStoreHook: () => createContextStoreHook
});
module.exports = __toCommonJS(createContextStoreHook_exports);
function createContextStoreHook(contextHook, contextKey) {
  function useStoreStoreHook(options) {
    const context = contextHook(options);
    if (!context) return null;
    return context[contextKey];
  }
  function useStoreHook(param) {
    let optional = false;
    let selector;
    if (typeof param === "function") {
      selector = param;
    } else if (param && typeof param === "object") {
      optional = !!param.optional;
      selector = param.selector;
    }
    const store = useStoreStoreHook({
      optional
    });
    if (!store) return null;
    return selector ? store(selector) : store();
  }
  return {
    [contextKey]: useStoreHook,
    [`${contextKey}Store`]: useStoreStoreHook
  };
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  createContextStoreHook
});
//# sourceMappingURL=createContextStoreHook.js.map