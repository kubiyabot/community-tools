// src/runtimes/edge/converters/fromLanguageModelTools.ts
var fromLanguageModelTools = (tools) => {
  return Object.fromEntries(
    tools.map((tool) => [
      tool.name,
      {
        description: tool.description,
        parameters: tool.parameters
      }
    ])
  );
};
export {
  fromLanguageModelTools
};
//# sourceMappingURL=fromLanguageModelTools.mjs.map