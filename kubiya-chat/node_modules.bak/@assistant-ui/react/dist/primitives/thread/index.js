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

// src/primitives/thread/index.ts
var thread_exports = {};
__export(thread_exports, {
  Empty: () => import_ThreadEmpty.ThreadPrimitiveEmpty,
  If: () => import_ThreadIf.ThreadPrimitiveIf,
  Messages: () => import_ThreadMessages.ThreadPrimitiveMessages,
  Root: () => import_ThreadRoot.ThreadPrimitiveRoot,
  ScrollToBottom: () => import_ThreadScrollToBottom.ThreadPrimitiveScrollToBottom,
  Suggestion: () => import_ThreadSuggestion.ThreadPrimitiveSuggestion,
  Viewport: () => import_ThreadViewport.ThreadPrimitiveViewport
});
module.exports = __toCommonJS(thread_exports);
var import_ThreadRoot = require("./ThreadRoot.js");
var import_ThreadEmpty = require("./ThreadEmpty.js");
var import_ThreadIf = require("./ThreadIf.js");
var import_ThreadViewport = require("./ThreadViewport.js");
var import_ThreadMessages = require("./ThreadMessages.js");
var import_ThreadScrollToBottom = require("./ThreadScrollToBottom.js");
var import_ThreadSuggestion = require("./ThreadSuggestion.js");
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  Empty,
  If,
  Messages,
  Root,
  ScrollToBottom,
  Suggestion,
  Viewport
});
//# sourceMappingURL=index.js.map