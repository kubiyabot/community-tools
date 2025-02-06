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

// src/primitives/thread/ThreadRoot.tsx
var ThreadRoot_exports = {};
__export(ThreadRoot_exports, {
  ThreadPrimitiveRoot: () => ThreadPrimitiveRoot
});
module.exports = __toCommonJS(ThreadRoot_exports);
var import_react_primitive = require("@radix-ui/react-primitive");
var import_react = require("react");
var import_jsx_runtime = require("react/jsx-runtime");
var ThreadPrimitiveRoot = (0, import_react.forwardRef)((props, ref) => {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(import_react_primitive.Primitive.div, { ...props, ref });
});
ThreadPrimitiveRoot.displayName = "ThreadPrimitive.Root";
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  ThreadPrimitiveRoot
});
//# sourceMappingURL=ThreadRoot.js.map