import { AssistantStreamChunk } from "./AssistantStreamChunkType";
import { StreamPart } from "./utils/StreamPart";
import { ToolResultStreamPart } from "./toolResultStream";
export declare function assistantEncoderStream(): TransformStream<ToolResultStreamPart, StreamPart<AssistantStreamChunk>>;
//# sourceMappingURL=assistantEncoderStream.d.ts.map