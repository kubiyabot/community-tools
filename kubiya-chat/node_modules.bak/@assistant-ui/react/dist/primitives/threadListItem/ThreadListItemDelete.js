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

// src/primitives/threadListItem/ThreadListItemDelete.ts
var ThreadListItemDelete_exports = {};
__export(ThreadListItemDelete_exports, {
  ThreadListItemPrimitiveDelete: () => ThreadListItemPrimitiveDelete
});
module.exports = __toCommonJS(ThreadListItemDelete_exports);
var import_createActionButton = require("../../utils/createActionButton.js");
var import_ThreadListItemContext = require("../../context/react/ThreadListItemContext.js");
var useThreadListItemDelete = () => {
  const runtime = (0, import_ThreadListItemContext.useThreadListItemRuntime)();
  return () => {
    runtime.delete();
  };
};
var ThreadListItemPrimitiveDelete = (0, import_createActionButton.createActionButton)(
  "ThreadListItemPrimitive.Delete",
  useThreadListItemDelete
);
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  ThreadListItemPrimitiveDelete
});
//# sourceMappingURL=ThreadListItemDelete.js.map