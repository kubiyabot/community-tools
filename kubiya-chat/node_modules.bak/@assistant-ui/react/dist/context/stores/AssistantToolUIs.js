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

// src/context/stores/AssistantToolUIs.ts
var AssistantToolUIs_exports = {};
__export(AssistantToolUIs_exports, {
  makeAssistantToolUIsStore: () => makeAssistantToolUIsStore
});
module.exports = __toCommonJS(AssistantToolUIs_exports);
var import_zustand = require("zustand");
var makeAssistantToolUIsStore = () => (0, import_zustand.create)((set) => {
  const renderers = /* @__PURE__ */ new Map();
  return Object.freeze({
    getToolUI: (name) => {
      const arr = renderers.get(name);
      const last = arr?.at(-1);
      if (last) return last;
      return null;
    },
    setToolUI: (name, render) => {
      let arr = renderers.get(name);
      if (!arr) {
        arr = [];
        renderers.set(name, arr);
      }
      arr.push(render);
      set({});
      return () => {
        const index = arr.indexOf(render);
        if (index !== -1) {
          arr.splice(index, 1);
        }
        if (index === arr.length) {
          set({});
        }
      };
    }
  });
});
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  makeAssistantToolUIsStore
});
//# sourceMappingURL=AssistantToolUIs.js.map