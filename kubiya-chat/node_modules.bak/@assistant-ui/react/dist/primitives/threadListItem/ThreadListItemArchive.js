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

// src/primitives/threadListItem/ThreadListItemArchive.ts
var ThreadListItemArchive_exports = {};
__export(ThreadListItemArchive_exports, {
  ThreadListItemPrimitiveArchive: () => ThreadListItemPrimitiveArchive
});
module.exports = __toCommonJS(ThreadListItemArchive_exports);
var import_createActionButton = require("../../utils/createActionButton.js");
var import_ThreadListItemContext = require("../../context/react/ThreadListItemContext.js");
var import_react = require("react");
var useThreadListItemArchive = () => {
  const runtime = (0, import_ThreadListItemContext.useThreadListItemRuntime)();
  return (0, import_react.useCallback)(() => {
    runtime.archive();
  }, [runtime]);
};
var ThreadListItemPrimitiveArchive = (0, import_createActionButton.createActionButton)(
  "ThreadListItemPrimitive.Archive",
  useThreadListItemArchive
);
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  ThreadListItemPrimitiveArchive
});
//# sourceMappingURL=ThreadListItemArchive.js.map