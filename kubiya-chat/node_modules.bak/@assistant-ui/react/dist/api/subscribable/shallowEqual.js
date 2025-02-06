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

// src/api/subscribable/shallowEqual.ts
var shallowEqual_exports = {};
__export(shallowEqual_exports, {
  shallowEqual: () => shallowEqual
});
module.exports = __toCommonJS(shallowEqual_exports);
function shallowEqual(objA, objB) {
  if (objA === void 0 && objB === void 0) return true;
  if (objA === void 0) return false;
  if (objB === void 0) return false;
  for (const key of Object.keys(objA)) {
    const valueA = objA[key];
    const valueB = objB[key];
    if (!Object.is(valueA, valueB)) return false;
  }
  return true;
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  shallowEqual
});
//# sourceMappingURL=shallowEqual.js.map