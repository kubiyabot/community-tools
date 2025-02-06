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

// src/utils/smooth/SmoothContext.tsx
var SmoothContext_exports = {};
__export(SmoothContext_exports, {
  SmoothContextProvider: () => SmoothContextProvider,
  useSmoothStatus: () => useSmoothStatus,
  useSmoothStatusStore: () => useSmoothStatusStore,
  withSmoothContextProvider: () => withSmoothContextProvider
});
module.exports = __toCommonJS(SmoothContext_exports);
var import_react = require("react");
var import_zustand = require("zustand");
var import_ContentPartContext = require("../../context/react/ContentPartContext.js");
var import_createContextStoreHook = require("../../context/react/utils/createContextStoreHook.js");
var import_jsx_runtime = require("react/jsx-runtime");
var SmoothContext = (0, import_react.createContext)(null);
var makeSmoothContext = (initialState) => {
  const useSmoothStatus2 = (0, import_zustand.create)(() => initialState);
  return { useSmoothStatus: useSmoothStatus2 };
};
var SmoothContextProvider = ({ children }) => {
  const outer = useSmoothContext({ optional: true });
  const contentPartRuntime = (0, import_ContentPartContext.useContentPartRuntime)();
  const [context] = (0, import_react.useState)(
    () => makeSmoothContext(contentPartRuntime.getState().status)
  );
  if (outer) return children;
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SmoothContext.Provider, { value: context, children });
};
var withSmoothContextProvider = (Component) => {
  const Wrapped = (0, import_react.forwardRef)((props, ref) => {
    return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SmoothContextProvider, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Component, { ...props, ref }) });
  });
  Wrapped.displayName = Component.displayName;
  return Wrapped;
};
function useSmoothContext(options) {
  const context = (0, import_react.useContext)(SmoothContext);
  if (!options?.optional && !context)
    throw new Error(
      "This component must be used within a SmoothContextProvider."
    );
  return context;
}
var { useSmoothStatus, useSmoothStatusStore } = (0, import_createContextStoreHook.createContextStoreHook)(
  useSmoothContext,
  "useSmoothStatus"
);
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  SmoothContextProvider,
  useSmoothStatus,
  useSmoothStatusStore,
  withSmoothContextProvider
});
//# sourceMappingURL=SmoothContext.js.map