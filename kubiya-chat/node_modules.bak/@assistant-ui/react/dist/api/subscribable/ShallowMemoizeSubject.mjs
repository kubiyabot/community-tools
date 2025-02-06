// src/api/subscribable/ShallowMemoizeSubject.ts
import { shallowEqual } from "./shallowEqual.mjs";
import { BaseSubject } from "./BaseSubject.mjs";
import { SKIP_UPDATE } from "./SKIP_UPDATE.mjs";
var ShallowMemoizeSubject = class extends BaseSubject {
  constructor(binding) {
    super();
    this.binding = binding;
    const state = binding.getState();
    if (state === SKIP_UPDATE)
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
    if (state === SKIP_UPDATE) return false;
    if (shallowEqual(state, this._previousState)) return false;
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
export {
  ShallowMemoizeSubject
};
//# sourceMappingURL=ShallowMemoizeSubject.mjs.map