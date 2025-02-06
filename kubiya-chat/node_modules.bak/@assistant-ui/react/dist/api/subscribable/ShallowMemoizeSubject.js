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

// src/api/subscribable/ShallowMemoizeSubject.ts
var ShallowMemoizeSubject_exports = {};
__export(ShallowMemoizeSubject_exports, {
  ShallowMemoizeSubject: () => ShallowMemoizeSubject
});
module.exports = __toCommonJS(ShallowMemoizeSubject_exports);
var import_shallowEqual = require("./shallowEqual.js");
var import_BaseSubject = require("./BaseSubject.js");
var import_SKIP_UPDATE = require("./SKIP_UPDATE.js");
var ShallowMemoizeSubject = class extends import_BaseSubject.BaseSubject {
  constructor(binding) {
    super();
    this.binding = binding;
    const state = binding.getState();
    if (state === import_SKIP_UPDATE.SKIP_UPDATE)
      throw new Error("Entry not available in the store");
    this._previousState = state;
  }
  get path() {
    return this.binding.path;
  }
  _previousState;
  getState = () => {
    if (!this.isConnected) this._syncState();
    return this._previousState;
  };
  _syncState() {
    const state = this.binding.getState();
    if (state === import_SKIP_UPDATE.SKIP_UPDATE) return false;
    if ((0, import_shallowEqual.shallowEqual)(state, this._previousState)) return false;
    this._previousState = state;
    return true;
  }
  _connect() {
    const callback = () => {
      if (this._syncState()) {
        this.notifySubscribers();
      }
    };
    return this.binding.subscribe(callback);
  }
};
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  ShallowMemoizeSubject
});
//# sourceMappingURL=ShallowMemoizeSubject.js.map