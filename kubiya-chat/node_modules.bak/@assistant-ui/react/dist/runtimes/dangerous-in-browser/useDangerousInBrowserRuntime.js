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

// src/runtimes/dangerous-in-browser/useDangerousInBrowserRuntime.ts
var useDangerousInBrowserRuntime_exports = {};
__export(useDangerousInBrowserRuntime_exports, {
  useDangerousInBrowserRuntime: () => useDangerousInBrowserRuntime
});
module.exports = __toCommonJS(useDangerousInBrowserRuntime_exports);
var import__ = require("../index.js");
var import_react = require("react");
var import_DangerousInBrowserAdapter = require("./DangerousInBrowserAdapter.js");
var import_LocalRuntimeOptions = require("../local/LocalRuntimeOptions.js");
var useDangerousInBrowserRuntime = (options) => {
  const { localRuntimeOptions, otherOptions } = (0, import_LocalRuntimeOptions.splitLocalRuntimeOptions)(options);
  const [adapter] = (0, import_react.useState)(() => new import_DangerousInBrowserAdapter.DangerousInBrowserAdapter(otherOptions));
  return (0, import__.useLocalRuntime)(adapter, localRuntimeOptions);
};
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  useDangerousInBrowserRuntime
});
//# sourceMappingURL=useDangerousInBrowserRuntime.js.map