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

// src/api/subscribable/BaseSubject.ts
var BaseSubject_exports = {};
__export(BaseSubject_exports, {
  BaseSubject: () => BaseSubject
});
module.exports = __toCommonJS(BaseSubject_exports);
var BaseSubject = class {
  _subscriptions = /* @__PURE__ */ new Set();
  _connection;
  get isConnected() {
    return !!this._connection;
  }
  notifySubscribers() {
    for (const callback of this._subscriptions) callback();
  }
  _updateConnection() {
    if (this._subscriptions.size > 0) {
      if (this._connection) return;
      this._connection = this._connect();
    } else {
      this._connection?.();
      this._connection = void 0;
    }
  }
  subscribe(callback) {
    this._subscriptions.add(callback);
    this._updateConnection();
    return () => {
      this._subscriptions.delete(callback);
      this._updateConnection();
    };
  }
};
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  BaseSubject
});
//# sourceMappingURL=BaseSubject.js.map