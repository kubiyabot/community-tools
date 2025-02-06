"use client";

// src/primitives/contentPart/ContentPartInProgress.tsx
import { useContentPart } from "../../context/index.mjs";
var ContentPartPrimitiveInProgress = ({ children }) => {
  const isInProgress = useContentPart((c) => c.status.type === "running");
  return isInProgress ? children : null;
};
ContentPartPrimitiveInProgress.displayName = "ContentPartPrimitive.InProgress";
export {
  ContentPartPrimitiveInProgress
};
//# sourceMappingURL=ContentPartInProgress.mjs.map