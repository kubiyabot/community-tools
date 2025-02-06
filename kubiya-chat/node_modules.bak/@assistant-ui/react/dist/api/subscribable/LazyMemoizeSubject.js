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

// src/api/subscribable/LazyMemoizeSubject.ts
var LazyMemoizeSubject_exports = {};
__export(LazyMemoizeSubject_exports, {
  LazyMemoizeSubject: () => LazyMemoizeSubject
});
module.exports = __toCommonJS(LazyMemoizeSubject_exports);
var import_BaseSubject = require("./BaseSubject.js");
var import_SKIP_UPDATE = require("./SKIP_UPDATE.js");
var LazyMemoizeSubject = class extends import_BaseSubject.BaseSubject {
  constructor(binding) {
    super();
    this.binding = binding;
  }
  get path() {
    return this.binding.path;
  }
  _previousStateDirty = true;
  _previousState;
  getState = () => {
    if (!this.isConnected || this._previousStateDirty) {
      const newState = this.binding.getState();
      if (newState !== import_SKIP_UPDATE.SKIP_UPDATE) {
        this._previousState = newState;
      }
      this._previousStateDirty = false;
    }
    if (this._previousState === void 0)
      throw new Error("Entry not available in the store");
    return this._previousState;
  };
  _connect() {
    const callback = () => {
      this._previousStateDirty = true;
      this.notifySubscribers();
    };
    return this.binding.subscribe(callback);
  }
};
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  LazyMemoizeSubject
});
//# sourceMappingURL=LazyMemoizeSubject.js.map