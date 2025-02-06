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

// src/primitives/threadListItem/index.ts
var threadListItem_exports = {};
__export(threadListItem_exports, {
  Archive: () => import_ThreadListItemArchive.ThreadListItemPrimitiveArchive,
  Delete: () => import_ThreadListItemDelete.ThreadListItemPrimitiveDelete,
  Root: () => import_ThreadListItemRoot.ThreadListItemPrimitiveRoot,
  Title: () => import_ThreadListItemTitle.ThreadListItemPrimitiveTitle,
  Trigger: () => import_ThreadListItemTrigger.ThreadListItemPrimitiveTrigger,
  Unarchive: () => import_ThreadListItemUnarchive.ThreadListItemPrimitiveUnarchive
});
module.exports = __toCommonJS(threadListItem_exports);
var import_ThreadListItemRoot = require("./ThreadListItemRoot.js");
var import_ThreadListItemArchive = require("./ThreadListItemArchive.js");
var import_ThreadListItemUnarchive = require("./ThreadListItemUnarchive.js");
var import_ThreadListItemDelete = require("./ThreadListItemDelete.js");
var import_ThreadListItemTrigger = require("./ThreadListItemTrigger.js");
var import_ThreadListItemTitle = require("./ThreadListItemTitle.js");
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  Archive,
  Delete,
  Root,
  Title,
  Trigger,
  Unarchive
});
//# sourceMappingURL=index.js.map