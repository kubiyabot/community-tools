"use strict";
"use client";
var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
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
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/primitives/assistantModal/AssistantModalContent.tsx
var AssistantModalContent_exports = {};
__export(AssistantModalContent_exports, {
  AssistantModalPrimitiveContent: () => AssistantModalPrimitiveContent
});
module.exports = __toCommonJS(AssistantModalContent_exports);
var import_react = require("react");
var PopoverPrimitive = __toESM(require("@radix-ui/react-popover"));
var import_scope = require("./scope.js");
var import_primitive = require("@radix-ui/primitive");
var import_jsx_runtime = require("react/jsx-runtime");
var AssistantModalPrimitiveContent = (0, import_react.forwardRef)(
  ({
    __scopeAssistantModal,
    side,
    align,
    onInteractOutside,
    dissmissOnInteractOutside = false,
    ...props
  }, forwardedRef) => {
    const scope = (0, import_scope.usePopoverScope)(__scopeAssistantModal);
    return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(PopoverPrimitive.Portal, { ...scope, children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
      PopoverPrimitive.Content,
      {
        ...scope,
        ...props,
        ref: forwardedRef,
        side: side ?? "top",
        align: align ?? "end",
        onInteractOutside: (0, import_primitive.composeEventHandlers)(
          onInteractOutside,
          dissmissOnInteractOutside ? void 0 : (e) => e.preventDefault()
        )
      }
    ) });
  }
);
AssistantModalPrimitiveContent.displayName = "AssistantModalPrimitive.Content";
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  AssistantModalPrimitiveContent
});
//# sourceMappingURL=AssistantModalContent.js.map