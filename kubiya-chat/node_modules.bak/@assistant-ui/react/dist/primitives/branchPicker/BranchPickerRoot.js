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

// src/primitives/branchPicker/BranchPickerRoot.tsx
var BranchPickerRoot_exports = {};
__export(BranchPickerRoot_exports, {
  BranchPickerPrimitiveRoot: () => BranchPickerPrimitiveRoot
});
module.exports = __toCommonJS(BranchPickerRoot_exports);
var import_react_primitive = require("@radix-ui/react-primitive");
var import_react = require("react");
var import_message = require("../message/index.js");
var import_jsx_runtime = require("react/jsx-runtime");
var BranchPickerPrimitiveRoot = (0, import_react.forwardRef)(({ hideWhenSingleBranch, ...rest }, ref) => {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(import_message.If, { hasBranches: hideWhenSingleBranch ? true : void 0, children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(import_react_primitive.Primitive.div, { ...rest, ref }) });
});
BranchPickerPrimitiveRoot.displayName = "BranchPickerPrimitive.Root";
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  BranchPickerPrimitiveRoot
});
//# sourceMappingURL=BranchPickerRoot.js.map