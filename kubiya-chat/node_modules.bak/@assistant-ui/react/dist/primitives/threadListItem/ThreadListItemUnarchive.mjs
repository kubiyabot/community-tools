"use client";

// src/primitives/threadListItem/ThreadListItemUnarchive.ts
import {
  createActionButton
} from "../../utils/createActionButton.mjs";
import { useThreadListItemRuntime } from "../../context/react/ThreadListItemContext.mjs";
var useThreadListItemUnarchive = () => {
  const runtime = useThreadListItemRuntime();
  return () => {
    runtime.unarchive();
  };
};
var ThreadListItemPrimitiveUnarchive = createActionButton(
  "ThreadListItemPrimitive.Unarchive",
  useThreadListItemUnarchive
);
export {
  ThreadListItemPrimitiveUnarchive
};
//# sourceMappingURL=ThreadListItemUnarchive.mjs.map