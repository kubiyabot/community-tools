"use client";

// src/runtimes/edge/useEdgeRuntime.ts
import { useLocalRuntime } from "../index.mjs";
import { EdgeChatAdapter } from "./EdgeChatAdapter.mjs";
import { splitLocalRuntimeOptions } from "../local/LocalRuntimeOptions.mjs";
var useEdgeRuntime = (options) => {
  const { localRuntimeOptions, otherOptions } = splitLocalRuntimeOptions(options);
  return useLocalRuntime(
    new EdgeChatAdapter(otherOptions),
    localRuntimeOptions
  );
};
export {
  useEdgeRuntime
};
//# sourceMappingURL=useEdgeRuntime.mjs.map