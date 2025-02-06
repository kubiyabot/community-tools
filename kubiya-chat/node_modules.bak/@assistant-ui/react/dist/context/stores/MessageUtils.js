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

// src/context/stores/MessageUtils.ts
var MessageUtils_exports = {};
__export(MessageUtils_exports, {
  makeMessageUtilsStore: () => makeMessageUtilsStore
});
module.exports = __toCommonJS(MessageUtils_exports);
var import_zustand = require("zustand");
var makeMessageUtilsStore = () => (0, import_zustand.create)((set) => {
  return {
    isCopied: false,
    setIsCopied: (value) => {
      set({ isCopied: value });
    },
    isHovering: false,
    setIsHovering: (value) => {
      set({ isHovering: value });
    }
  };
});
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  makeMessageUtilsStore
});
//# sourceMappingURL=MessageUtils.js.map