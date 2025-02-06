// src/runtimes/edge/streams/utils/chunkByLineStream.ts
function chunkByLineStream() {
  let buffer = "";
  return new TransformStream({
    transform(chunk, controller) {
      buffer += chunk;
      const lines = buffer.split("\n");
      for (let i = 0; i < lines.length - 1; i++) {
        controller.enqueue(lines[i]);
      }
      buffer = lines[lines.length - 1];
    },
    flush(controller) {
      if (buffer) {
        controller.enqueue(buffer);
      }
    }
  });
}
export {
  chunkByLineStream
};
//# sourceMappingURL=chunkByLineStream.mjs.map