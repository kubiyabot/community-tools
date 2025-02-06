"use client";

// src/primitives/threadListItem/ThreadListItemTitle.tsx
import { useThreadListItem } from "../../context/react/ThreadListItemContext.mjs";
import { Fragment, jsx } from "react/jsx-runtime";
var ThreadListItemPrimitiveTitle = ({ fallback }) => {
  const title = useThreadListItem((t) => t.title);
  return /* @__PURE__ */ jsx(Fragment, { children: title || fallback });
};
ThreadListItemPrimitiveTitle.displayName = "ThreadListItemPrimitive.Title";
export {
  ThreadListItemPrimitiveTitle
};
//# sourceMappingURL=ThreadListItemTitle.mjs.map