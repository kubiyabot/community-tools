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

// src/runtimes/edge/useEdgeRuntime.ts
var useEdgeRuntime_exports = {};
__export(useEdgeRuntime_exports, {
  useEdgeRuntime: () => useEdgeRuntime
});
module.exports = __toCommonJS(useEdgeRuntime_exports);
var import__ = require("../index.js");
var import_EdgeChatAdapter = require("./EdgeChatAdapter.js");
var import_LocalRuntimeOptions = require("../local/LocalRuntimeOptions.js");
var useEdgeRuntime = (options) => {
  const { localRuntimeOptions, otherOptions } = (0, import_LocalRuntimeOptions.splitLocalRuntimeOptions)(options);
  return (0, import__.useLocalRuntime)(
    new import_EdgeChatAdapter.EdgeChatAdapter(otherOptions),
    localRuntimeOptions
  );
};
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  useEdgeRuntime
});
//# sourceMappingURL=useEdgeRuntime.js.map