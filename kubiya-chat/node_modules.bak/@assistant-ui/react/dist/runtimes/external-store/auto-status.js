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

// src/runtimes/external-store/auto-status.tsx
var auto_status_exports = {};
__export(auto_status_exports, {
  getAutoStatus: () => getAutoStatus,
  isAutoStatus: () => isAutoStatus
});
module.exports = __toCommonJS(auto_status_exports);
var AUTO_STATUS_RUNNING = Object.freeze({ type: "running" });
var AUTO_STATUS_COMPLETE = Object.freeze({
  type: "complete",
  reason: "unknown"
});
var isAutoStatus = (status) => status === AUTO_STATUS_RUNNING || status === AUTO_STATUS_COMPLETE;
var getAutoStatus = (isLast, isRunning) => isLast && isRunning ? AUTO_STATUS_RUNNING : AUTO_STATUS_COMPLETE;
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  getAutoStatus,
  isAutoStatus
});
//# sourceMappingURL=auto-status.js.map