import { z } from 'zod';

export const sourceFormSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  url: z.string().min(1, 'URL is required'),
  runner: z.string().optional(),
  branch: z.string().optional(),
  dynamic_config: z.any().optional()
});

export type FormValues = z.infer<typeof sourceFormSchema>;

// Add cache-related schemas
export const sourceCacheSchema = z.object({
  data: z.any(),
  timestamp: z.number(),
  version: z.string().optional()
});

export const cacheInvalidationSchema = z.object({
  pattern: z.string().optional(),
  sourceId: z.string().optional()
});

export type SourceCache = z.infer<typeof sourceCacheSchema>;
export type CacheInvalidation = z.infer<typeof cacheInvalidationSchema>; 