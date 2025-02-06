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

// src/primitives/actionBar/ActionBarRoot.tsx
var ActionBarRoot_exports = {};
__export(ActionBarRoot_exports, {
  ActionBarPrimitiveRoot: () => ActionBarPrimitiveRoot
});
module.exports = __toCommonJS(ActionBarRoot_exports);
var import_react_primitive = require("@radix-ui/react-primitive");
var import_react = require("react");
var import_useActionBarFloatStatus = require("./useActionBarFloatStatus.js");
var import_jsx_runtime = require("react/jsx-runtime");
var ActionBarPrimitiveRoot = (0, import_react.forwardRef)(({ hideWhenRunning, autohide, autohideFloat, ...rest }, ref) => {
  const hideAndfloatStatus = (0, import_useActionBarFloatStatus.useActionBarFloatStatus)({
    hideWhenRunning,
    autohide,
    autohideFloat
  });
  if (hideAndfloatStatus === import_useActionBarFloatStatus.HideAndFloatStatus.Hidden) return null;
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
    import_react_primitive.Primitive.div,
    {
      ...hideAndfloatStatus === import_useActionBarFloatStatus.HideAndFloatStatus.Floating ? { "data-floating": "true" } : null,
      ...rest,
      ref
    }
  );
});
ActionBarPrimitiveRoot.displayName = "ActionBarPrimitive.Root";
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  ActionBarPrimitiveRoot
});
//# sourceMappingURL=ActionBarRoot.js.map