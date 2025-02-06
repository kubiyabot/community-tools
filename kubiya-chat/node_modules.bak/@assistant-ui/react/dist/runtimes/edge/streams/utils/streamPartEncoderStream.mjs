// src/runtimes/edge/streams/utils/streamPartEncoderStream.ts
import { PipeableTransformStream } from "./PipeableTransformStream.mjs";
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
  return new PipeableTransformStream((readable) => {
    return readable.pipeThrough(encodeStream).pipeThrough(new TextEncoderStream());
  });
}
export {
  streamPartEncoderStream
};
//# sourceMappingURL=streamPartEncoderStream.mjs.map