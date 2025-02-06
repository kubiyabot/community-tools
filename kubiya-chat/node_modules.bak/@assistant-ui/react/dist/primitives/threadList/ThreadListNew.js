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

// src/primitives/threadList/ThreadListNew.tsx
var ThreadListNew_exports = {};
__export(ThreadListNew_exports, {
  ThreadListPrimitiveNew: () => ThreadListPrimitiveNew
});
module.exports = __toCommonJS(ThreadListNew_exports);
var import_context = require("../../context/index.js");
var import_react = require("react");
var import_react_primitive = require("@radix-ui/react-primitive");
var import_primitive = require("@radix-ui/primitive");
var import_jsx_runtime = require("react/jsx-runtime");
var useThreadListNew = () => {
  const runtime = (0, import_context.useAssistantRuntime)();
  return () => {
    runtime.switchToNewThread();
  };
};
var ThreadListPrimitiveNew = (0, import_react.forwardRef)(({ onClick, disabled, ...props }, forwardedRef) => {
  const isMain = (0, import_context.useThreadList)((t) => t.newThread === t.mainThreadId);
  const callback = useThreadListNew();
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
    import_react_primitive.Primitive.button,
    {
      type: "button",
      ...isMain ? { "data-active": "true", "aria-current": "true" } : null,
      ...props,
      ref: forwardedRef,
      disabled: disabled || !callback,
      onClick: (0, import_primitive.composeEventHandlers)(onClick, () => {
        callback?.();
      })
    }
  );
});
ThreadListPrimitiveNew.displayName = "ThreadListPrimitive.New";
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  ThreadListPrimitiveNew
});
//# sourceMappingURL=ThreadListNew.js.map