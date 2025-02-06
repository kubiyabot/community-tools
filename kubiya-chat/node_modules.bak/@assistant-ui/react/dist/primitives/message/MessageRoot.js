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

// src/primitives/message/MessageRoot.tsx
var MessageRoot_exports = {};
__export(MessageRoot_exports, {
  MessagePrimitiveRoot: () => MessagePrimitiveRoot
});
module.exports = __toCommonJS(MessageRoot_exports);
var import_react_primitive = require("@radix-ui/react-primitive");
var import_react = require("react");
var import_MessageContext = require("../../context/react/MessageContext.js");
var import_useManagedRef = require("../../utils/hooks/useManagedRef.js");
var import_react_compose_refs = require("@radix-ui/react-compose-refs");
var import_jsx_runtime = require("react/jsx-runtime");
var useIsHoveringRef = () => {
  const messageUtilsStore = (0, import_MessageContext.useMessageUtilsStore)();
  const callbackRef = (0, import_react.useCallback)(
    (el) => {
      const setIsHovering = messageUtilsStore.getState().setIsHovering;
      const handleMouseEnter = () => {
        setIsHovering(true);
      };
      const handleMouseLeave = () => {
        setIsHovering(false);
      };
      el.addEventListener("mouseenter", handleMouseEnter);
      el.addEventListener("mouseleave", handleMouseLeave);
      return () => {
        el.removeEventListener("mouseenter", handleMouseEnter);
        el.removeEventListener("mouseleave", handleMouseLeave);
        setIsHovering(false);
      };
    },
    [messageUtilsStore]
  );
  return (0, import_useManagedRef.useManagedRef)(callbackRef);
};
var MessagePrimitiveRoot = (0, import_react.forwardRef)((props, forwardRef2) => {
  const isHoveringRef = useIsHoveringRef();
  const ref = (0, import_react_compose_refs.useComposedRefs)(forwardRef2, isHoveringRef);
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(import_react_primitive.Primitive.div, { ...props, ref });
});
MessagePrimitiveRoot.displayName = "MessagePrimitive.Root";
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  MessagePrimitiveRoot
});
//# sourceMappingURL=MessageRoot.js.map