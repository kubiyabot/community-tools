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

// src/utils/smooth/index.ts
var smooth_exports = {};
__export(smooth_exports, {
  useSmooth: () => import_useSmooth.useSmooth,
  useSmoothStatus: () => import_SmoothContext.useSmoothStatus,
  withSmoothContextProvider: () => import_SmoothContext.withSmoothContextProvider
});
module.exports = __toCommonJS(smooth_exports);
var import_useSmooth = require("./useSmooth.js");
var import_SmoothContext = require("./SmoothContext.js");
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  useSmooth,
  useSmoothStatus,
  withSmoothContextProvider
});
//# sourceMappingURL=index.js.map