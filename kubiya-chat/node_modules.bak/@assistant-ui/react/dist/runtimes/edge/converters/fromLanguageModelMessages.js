"use strict";
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/runtimes/edge/converters/fromLanguageModelMessages.ts
var fromLanguageModelMessages_exports = {};
__export(fromLanguageModelMessages_exports, {
  fromLanguageModelMessages: () => fromLanguageModelMessages
});
module.exports = __toCommonJS(fromLanguageModelMessages_exports);
var fromLanguageModelMessages = (lm, { mergeSteps }) => {
  const messages = [];
  for (const lmMessage of lm) {
    const role = lmMessage.role;
    switch (role) {
      case "system": {
        messages.push({
          role: "system",
          content: [
            {
              type: "text",
              text: lmMessage.content
            }
          ]
        });
        break;
      }
      case "user": {
        messages.push({
          role: "user",
          content: lmMessage.content.map((part) => {
            const type = part.type;
            switch (type) {
              case "text": {
                return {
                  type: "text",
                  text: part.text
                };
              }
              case "image": {
                if (part.image instanceof URL) {
                  return {
                    type: "image",
                    image: part.image.href
                  };
                }
                throw new Error("Only images with URL data are supported");
              }
              case "file": {
                if (part.data instanceof URL) {
                  return {
                    type: "file",
                    data: part.data.href,
                    mimeType: part.mimeType
                  };
                }
                throw new Error("Only files with URL data are supported");
              }
              default: {
                const unhandledType = type;
                throw new Error(`Unknown content part type: ${unhandledType}`);
              }
            }
          })
        });
        break;
      }
      case "assistant": {
        const newContent = lmMessage.content.map((part) => {
          if (part.type === "tool-call") {
            return {
              type: "tool-call",
              toolCallId: part.toolCallId,
              toolName: part.toolName,
              argsText: JSON.stringify(part.args),
              args: part.args
            };
          }
          return part;
        });
        if (mergeSteps) {
          const previousMessage = messages[messages.length - 1];
          if (previousMessage?.role === "assistant") {
            previousMessage.content = [
              ...previousMessage.content,
              ...newContent
            ];
            break;
          }
        }
        messages.push({
          role: "assistant",
          content: newContent
        });
        break;
      }
      case "tool": {
        const previousMessage = messages[messages.length - 1];
        if (previousMessage?.role !== "assistant")
          throw new Error(
            "A tool message must be preceded by an assistant message."
          );
        for (const tool of lmMessage.content) {
          const toolCall = previousMessage.content.find(
            (c) => c.type === "tool-call" && c.toolCallId === tool.toolCallId
          );
          if (!toolCall)
            throw new Error("Received tool result for an unknown tool call.");
          if (toolCall.toolName !== tool.toolName)
            throw new Error("Tool call name mismatch.");
          const writable = toolCall;
          writable.result = tool.result;
          if (tool.isError) {
            writable.isError = true;
          }
        }
        break;
      }
      default: {
        const unhandledRole = role;
        throw new Error(`Unknown message role: ${unhandledRole}`);
      }
    }
  }
  return messages;
};
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  fromLanguageModelMessages
});
//# sourceMappingURL=fromLanguageModelMessages.js.map