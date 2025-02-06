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

// src/utils/combined/createCombinedStore.ts
var createCombinedStore_exports = {};
__export(createCombinedStore_exports, {
  createCombinedStore: () => createCombinedStore
});
module.exports = __toCommonJS(createCombinedStore_exports);
var import_react = require("react");
var createCombinedStore = (stores) => {
  const subscribe = (callback) => {
    const unsubscribes = stores.map((store) => store.subscribe(callback));
    return () => {
      for (const unsub of unsubscribes) {
        unsub();
      }
    };
  };
  return (selector) => {
    const getSnapshot = () => selector(...stores.map((store) => store.getState()));
    return (0, import_react.useSyncExternalStore)(subscribe, getSnapshot, getSnapshot);
  };
};
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  createCombinedStore
});
//# sourceMappingURL=createCombinedStore.js.map