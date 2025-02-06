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

// src/primitives/actionBar/useActionBarFloatStatus.tsx
var useActionBarFloatStatus_exports = {};
__export(useActionBarFloatStatus_exports, {
  HideAndFloatStatus: () => HideAndFloatStatus,
  useActionBarFloatStatus: () => useActionBarFloatStatus
});
module.exports = __toCommonJS(useActionBarFloatStatus_exports);
var import_MessageContext = require("../../context/react/MessageContext.js");
var import_ThreadContext = require("../../context/react/ThreadContext.js");
var import_useCombinedStore = require("../../utils/combined/useCombinedStore.js");
var HideAndFloatStatus = /* @__PURE__ */ ((HideAndFloatStatus2) => {
  HideAndFloatStatus2["Hidden"] = "hidden";
  HideAndFloatStatus2["Floating"] = "floating";
  HideAndFloatStatus2["Normal"] = "normal";
  return HideAndFloatStatus2;
})(HideAndFloatStatus || {});
var useActionBarFloatStatus = ({
  hideWhenRunning,
  autohide,
  autohideFloat
}) => {
  const threadRuntime = (0, import_ThreadContext.useThreadRuntime)();
  const messageRuntime = (0, import_MessageContext.useMessageRuntime)();
  const messageUtilsStore = (0, import_MessageContext.useMessageUtilsStore)();
  return (0, import_useCombinedStore.useCombinedStore)(
    [threadRuntime, messageRuntime, messageUtilsStore],
    (t, m, mu) => {
      if (hideWhenRunning && t.isRunning) return "hidden" /* Hidden */;
      const autohideEnabled = autohide === "always" || autohide === "not-last" && !m.isLast;
      if (!autohideEnabled) return "normal" /* Normal */;
      if (!mu.isHovering) return "hidden" /* Hidden */;
      if (autohideFloat === "always" || autohideFloat === "single-branch" && m.branchCount <= 1)
        return "floating" /* Floating */;
      return "normal" /* Normal */;
    }
  );
};
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  HideAndFloatStatus,
  useActionBarFloatStatus
});
//# sourceMappingURL=useActionBarFloatStatus.js.map