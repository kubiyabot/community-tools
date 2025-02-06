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

// src/primitives/branchPicker/index.ts
var branchPicker_exports = {};
__export(branchPicker_exports, {
  Count: () => import_BranchPickerCount.BranchPickerPrimitiveCount,
  Next: () => import_BranchPickerNext.BranchPickerPrimitiveNext,
  Number: () => import_BranchPickerNumber.BranchPickerPrimitiveNumber,
  Previous: () => import_BranchPickerPrevious.BranchPickerPrimitivePrevious,
  Root: () => import_BranchPickerRoot.BranchPickerPrimitiveRoot
});
module.exports = __toCommonJS(branchPicker_exports);
var import_BranchPickerNext = require("./BranchPickerNext.js");
var import_BranchPickerPrevious = require("./BranchPickerPrevious.js");
var import_BranchPickerCount = require("./BranchPickerCount.js");
var import_BranchPickerNumber = require("./BranchPickerNumber.js");
var import_BranchPickerRoot = require("./BranchPickerRoot.js");
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  Count,
  Next,
  Number,
  Previous,
  Root
});
//# sourceMappingURL=index.js.map