import { AssistantStreamChunk } from "./AssistantStreamChunkType";
import { StreamPart } from "./utils/StreamPart";
import { ToolResultStreamPart } from "./toolResultStream";
export declare function assistantDecoderStream(): TransformStream<StreamPart<AssistantStreamChunk>, ToolResultStreamPart>;
//# sourceMappingURL=assistantDecoderStream.d.ts.map