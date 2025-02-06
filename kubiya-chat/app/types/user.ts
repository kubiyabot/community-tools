export interface User {
  _id: string;
  create_at: string;
  email: string;
  groups: string[];
  image: string;
  invite_link: string;
  name: string;
  roles: string[] | null;
  status: boolean;
  user_groups: string[] | null;
  user_status: 'active' | 'pending';
  uuid: string;
}

export interface PaginatedResponse<T> {
  pagination: {
    limit: number;
    page: number;
    total_items: number;
    next_page: number | null;
    prev_page: number | null;
  };
  items: T[];
}

export type PaginatedUsers = PaginatedResponse<User>;

export interface Group {
  uuid: string;
  name: string;
  description: string;
  system: boolean;
  create_at: string;
  roles: string[] | null;
}

export interface EntityMetadata {
  uuid: string;
  name: string;
  image?: string;
  description?: string;
  type: 'user' | 'group' | 'unknown';
  status?: 'active' | 'pending';
  create_at?: string;
  email?: string;
} 