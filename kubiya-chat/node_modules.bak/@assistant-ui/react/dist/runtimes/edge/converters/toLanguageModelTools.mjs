// src/runtimes/edge/converters/toLanguageModelTools.ts
import { z } from "zod";
import zodToJsonSchema from "zod-to-json-schema";
var toLanguageModelTools = (tools) => {
  return Object.entries(tools).map(([name, tool]) => ({
    type: "function",
    name,
    ...tool.description ? { description: tool.description } : void 0,
    parameters: tool.parameters instanceof z.ZodType ? zodToJsonSchema(tool.parameters) : tool.parameters
  }));
};
export {
  toLanguageModelTools
};
//# sourceMappingURL=toLanguageModelTools.mjs.map