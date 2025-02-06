// src/runtimes/external-store/auto-status.tsx
var AUTO_STATUS_RUNNING = Object.freeze({ type: "running" });
var AUTO_STATUS_COMPLETE = Object.freeze({
  type: "complete",
  reason: "unknown"
});
var isAutoStatus = (status) => status === AUTO_STATUS_RUNNING || status === AUTO_STATUS_COMPLETE;
var getAutoStatus = (isLast, isRunning) => isLast && isRunning ? AUTO_STATUS_RUNNING : AUTO_STATUS_COMPLETE;
export {
  getAutoStatus,
  isAutoStatus
};
//# sourceMappingURL=auto-status.mjs.map