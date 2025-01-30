export interface ToolArgument {
  name: string;
  type: string;
  description: string;
  required?: boolean;
  default?: any;
  enum?: any[];
  pattern?: string;
  min?: number;
  max?: number;
  minLength?: number;
  maxLength?: number;
}

export interface Tool {
  uuid?: string;
  name: string;
  alias?: string;
  description: string;
  type?: string;
  icon_url?: string;
  args?: ToolArgument[];
  secrets?: string[];
  env?: string[];
  image?: string;
  workdir?: string;
  code?: string;
  content?: string;
  mermaid?: string;
  mounts?: Array<string | { source: string; target: string }>;
  with_files?: Array<{
    source: string;
    target: string;
    content?: string;
  }>;
  with_volumes?: any;
  metadata?: Record<string, any>;
  source?: {
    id: string;
    name: string;
    url: string;
    metadata?: {
      git_branch?: string;
      git_commit?: string;
      last_updated?: string;
    };
  };
} 