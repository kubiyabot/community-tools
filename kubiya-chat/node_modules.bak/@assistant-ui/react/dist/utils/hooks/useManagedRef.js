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

// src/utils/hooks/useManagedRef.ts
var useManagedRef_exports = {};
__export(useManagedRef_exports, {
  useManagedRef: () => useManagedRef
});
module.exports = __toCommonJS(useManagedRef_exports);
var import_react = require("react");
var useManagedRef = (callback) => {
  const cleanupRef = (0, import_react.useRef)(void 0);
  const ref = (0, import_react.useCallback)(
    (el) => {
      if (cleanupRef.current) {
        cleanupRef.current();
      }
      if (el) {
        cleanupRef.current = callback(el);
      }
    },
    [callback]
  );
  return ref;
};
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  useManagedRef
});
//# sourceMappingURL=useManagedRef.js.map