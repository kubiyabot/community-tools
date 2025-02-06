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

// src/utils/createActionButton.tsx
var createActionButton_exports = {};
__export(createActionButton_exports, {
  createActionButton: () => createActionButton
});
module.exports = __toCommonJS(createActionButton_exports);
var import_react = require("react");
var import_react_primitive = require("@radix-ui/react-primitive");
var import_primitive = require("@radix-ui/primitive");
var import_jsx_runtime = require("react/jsx-runtime");
var createActionButton = (displayName, useActionButton, forwardProps = []) => {
  const ActionButton = (0, import_react.forwardRef)((props, forwardedRef) => {
    const forwardedProps = {};
    const primitiveProps = {};
    Object.keys(props).forEach((key) => {
      if (forwardProps.includes(key)) {
        forwardedProps[key] = props[key];
      } else {
        primitiveProps[key] = props[key];
      }
    });
    const callback = useActionButton(forwardedProps) ?? void 0;
    return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
      import_react_primitive.Primitive.button,
      {
        type: "button",
        ...primitiveProps,
        ref: forwardedRef,
        disabled: primitiveProps.disabled || !callback,
        onClick: (0, import_primitive.composeEventHandlers)(primitiveProps.onClick, callback)
      }
    );
  });
  ActionButton.displayName = displayName;
  return ActionButton;
};
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  createActionButton
});
//# sourceMappingURL=createActionButton.js.map