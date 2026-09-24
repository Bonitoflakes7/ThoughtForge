export type ForkType = "support" | "challenge" | "refine" | "extend";

export type User = {
  id: string;
  username: string;
  email: string;
  display_name: string;
  bio: string | null;
  avatar_url: string | null;
  role: "user" | "moderator" | "admin";
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
};

export type Author = Pick<User, "id" | "username" | "display_name">;

export type Thought = {
  id: string;
  parent_thought_id: string | null;
  title: string;
  body: string;
  fork_type: ForkType | null;
  author: Author;
  like_count: number;
  comment_count: number;
  fork_count: number;
  created_at: string;
  updated_at: string;
  is_deleted: boolean;
};

export type Comment = {
  id: string;
  thought_id: string;
  body: string;
  author: Author;
  like_count: number;
  created_at: string;
  is_deleted: boolean;
};

export type ThoughtDetail = Thought & { comments: Comment[]; forks: Thought[] };

export type Report = {
  id: string;
  reporter_id: string;
  target_type: "thought" | "comment";
  target_id: string;
  reason: string;
  details: string | null;
  status: "open" | "resolved" | "dismissed";
  resolution_note: string | null;
  created_at: string;
  resolved_by_id: string | null;
};
