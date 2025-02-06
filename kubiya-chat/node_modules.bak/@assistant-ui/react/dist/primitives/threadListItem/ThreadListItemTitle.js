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

// src/primitives/threadListItem/ThreadListItemTitle.tsx
var ThreadListItemTitle_exports = {};
__export(ThreadListItemTitle_exports, {
  ThreadListItemPrimitiveTitle: () => ThreadListItemPrimitiveTitle
});
module.exports = __toCommonJS(ThreadListItemTitle_exports);
var import_ThreadListItemContext = require("../../context/react/ThreadListItemContext.js");
var import_jsx_runtime = require("react/jsx-runtime");
var ThreadListItemPrimitiveTitle = ({ fallback }) => {
  const title = (0, import_ThreadListItemContext.useThreadListItem)((t) => t.title);
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(import_jsx_runtime.Fragment, { children: title || fallback });
};
ThreadListItemPrimitiveTitle.displayName = "ThreadListItemPrimitive.Title";
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  ThreadListItemPrimitiveTitle
});
//# sourceMappingURL=ThreadListItemTitle.js.map