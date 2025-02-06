"use client";

// src/primitives/threadListItem/ThreadListItemTrigger.ts
import {
  createActionButton
} from "../../utils/createActionButton.mjs";
import { useThreadListItemRuntime } from "../../context/react/ThreadListItemContext.mjs";
var useThreadListItemTrigger = () => {
  const runtime = useThreadListItemRuntime();
  return () => {
    runtime.switchTo();
  };
};
var ThreadListItemPrimitiveTrigger = createActionButton(
  "ThreadListItemPrimitive.Trigger",
  useThreadListItemTrigger
);
export {
  ThreadListItemPrimitiveTrigger
};
//# sourceMappingURL=ThreadListItemTrigger.mjs.map