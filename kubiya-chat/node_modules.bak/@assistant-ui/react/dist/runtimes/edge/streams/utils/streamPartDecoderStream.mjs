// src/runtimes/edge/streams/utils/streamPartDecoderStream.ts
import { chunkByLineStream } from "./chunkByLineStream.mjs";
import { PipeableTransformStream } from "./PipeableTransformStream.mjs";
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
  return new PipeableTransformStream((readable) => {
    return readable.pipeThrough(new TextDecoderStream()).pipeThrough(chunkByLineStream()).pipeThrough(decodeStream);
  });
}
export {
  streamPartDecoderStream
};
//# sourceMappingURL=streamPartDecoderStream.mjs.map