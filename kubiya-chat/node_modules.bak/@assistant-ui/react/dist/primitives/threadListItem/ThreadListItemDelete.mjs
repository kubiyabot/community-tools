"use client";

// src/primitives/threadListItem/ThreadListItemDelete.ts
import {
  createActionButton
} from "../../utils/createActionButton.mjs";
import { useThreadListItemRuntime } from "../../context/react/ThreadListItemContext.mjs";
var useThreadListItemDelete = () => {
  const runtime = useThreadListItemRuntime();
  return () => {
    runtime.delete();
  };
};
var ThreadListItemPrimitiveDelete = createActionButton(
  "ThreadListItemPrimitive.Delete",
  useThreadListItemDelete
);
export {
  ThreadListItemPrimitiveDelete
};
//# sourceMappingURL=ThreadListItemDelete.mjs.map