"use client";

// src/runtimes/dangerous-in-browser/useDangerousInBrowserRuntime.ts
import { useLocalRuntime } from "../index.mjs";
import { useState } from "react";
import {
  DangerousInBrowserAdapter
} from "./DangerousInBrowserAdapter.mjs";
import { splitLocalRuntimeOptions } from "../local/LocalRuntimeOptions.mjs";
var useDangerousInBrowserRuntime = (options) => {
  const { localRuntimeOptions, otherOptions } = splitLocalRuntimeOptions(options);
  const [adapter] = useState(() => new DangerousInBrowserAdapter(otherOptions));
  return useLocalRuntime(adapter, localRuntimeOptions);
};
export {
  useDangerousInBrowserRuntime
};
//# sourceMappingURL=useDangerousInBrowserRuntime.mjs.map