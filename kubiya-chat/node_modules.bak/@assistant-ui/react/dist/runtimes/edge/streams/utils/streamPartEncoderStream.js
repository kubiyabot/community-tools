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

// src/runtimes/edge/streams/utils/streamPartEncoderStream.ts
var streamPartEncoderStream_exports = {};
__export(streamPartEncoderStream_exports, {
  streamPartEncoderStream: () => streamPartEncoderStream
});
module.exports = __toCommonJS(streamPartEncoderStream_exports);
var import_PipeableTransformStream = require("./PipeableTransformStream.js");
function encodeStreamPart({
  type,
  value
}) {
  return `${type}:${JSON.stringify(value)}
`;
}
function streamPartEncoderStream() {
  const encodeStream = new TransformStream({
    transform(chunk, controller) {
      controller.enqueue(encodeStreamPart(chunk));
    }
  });
  return new import_PipeableTransformStream.PipeableTransformStream((readable) => {
    return readable.pipeThrough(encodeStream).pipeThrough(new TextEncoderStream());
  });
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  streamPartEncoderStream
});
//# sourceMappingURL=streamPartEncoderStream.js.map