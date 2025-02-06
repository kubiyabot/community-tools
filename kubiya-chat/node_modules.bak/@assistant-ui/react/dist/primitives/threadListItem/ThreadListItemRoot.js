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

// src/primitives/threadListItem/ThreadListItemRoot.tsx
var ThreadListItemRoot_exports = {};
__export(ThreadListItemRoot_exports, {
  ThreadListItemPrimitiveRoot: () => ThreadListItemPrimitiveRoot
});
module.exports = __toCommonJS(ThreadListItemRoot_exports);
var import_react_primitive = require("@radix-ui/react-primitive");
var import_react = require("react");
var import_ThreadListItemContext = require("../../context/react/ThreadListItemContext.js");
var import_jsx_runtime = require("react/jsx-runtime");
var ThreadListItemPrimitiveRoot = (0, import_react.forwardRef)((props, ref) => {
  const isMain = (0, import_ThreadListItemContext.useThreadListItem)((t) => t.isMain);
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
    import_react_primitive.Primitive.div,
    {
      ...isMain ? { "data-active": "true", "aria-current": "true" } : null,
      ...props,
      ref
    }
  );
});
ThreadListItemPrimitiveRoot.displayName = "ThreadListItemPrimitive.Root";
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  ThreadListItemPrimitiveRoot
});
//# sourceMappingURL=ThreadListItemRoot.js.map