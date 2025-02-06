"use client";

// src/primitives/threadListItem/ThreadListItemArchive.ts
import {
  createActionButton
} from "../../utils/createActionButton.mjs";
import { useThreadListItemRuntime } from "../../context/react/ThreadListItemContext.mjs";
import { useCallback } from "react";
var useThreadListItemArchive = () => {
  const runtime = useThreadListItemRuntime();
  return useCallback(() => {
    runtime.archive();
  }, [runtime]);
};
var ThreadListItemPrimitiveArchive = createActionButton(
  "ThreadListItemPrimitive.Archive",
  useThreadListItemArchive
);
export {
  ThreadListItemPrimitiveArchive
};
//# sourceMappingURL=ThreadListItemArchive.mjs.map