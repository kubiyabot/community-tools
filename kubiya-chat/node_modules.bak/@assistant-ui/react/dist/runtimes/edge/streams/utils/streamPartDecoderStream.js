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

// src/runtimes/edge/streams/utils/streamPartDecoderStream.ts
var streamPartDecoderStream_exports = {};
__export(streamPartDecoderStream_exports, {
  streamPartDecoderStream: () => streamPartDecoderStream
});
module.exports = __toCommonJS(streamPartDecoderStream_exports);
var import_chunkByLineStream = require("./chunkByLineStream.js");
var import_PipeableTransformStream = require("./PipeableTransformStream.js");
var decodeStreamPart = (part) => {
  const index = part.indexOf(":");
  if (index === -1) throw new Error("Invalid stream part");
  return {
    type: part.slice(0, index),
    value: JSON.parse(part.slice(index + 1))
  };
};
function streamPartDecoderStream() {
  const decodeStream = new TransformStream({
    transform(chunk, controller) {
      controller.enqueue(decodeStreamPart(chunk));
    }
  });
  return new import_PipeableTransformStream.PipeableTransformStream((readable) => {
    return readable.pipeThrough(new TextDecoderStream()).pipeThrough((0, import_chunkByLineStream.chunkByLineStream)()).pipeThrough(decodeStream);
  });
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  streamPartDecoderStream
});
//# sourceMappingURL=streamPartDecoderStream.js.map