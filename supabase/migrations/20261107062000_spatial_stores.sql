-- Add store separation without replacing existing tasks or the default workspace.
alter table public.spatial_demo_tasks add column if not exists store_id text not null default 'myeongdong';
create index if not exists spatial_demo_tasks_store_idx on public.spatial_demo_tasks(workspace_id,store_id,created_at desc);
create table if not exists public.spatial_demo_stores (
  workspace_id uuid not null,
  id text not null,
  payload jsonb not null,
  revision integer not null default 1,
  updated_at timestamptz not null default now(),
  primary key(workspace_id,id),
  constraint store_payload_bounded check(octet_length(payload::text)<2200000)
);
alter table public.spatial_demo_stores enable row level security;
revoke all on public.spatial_demo_stores from anon,authenticated;
grant select,insert,update on public.spatial_demo_stores to service_role;
comment on table public.spatial_demo_stores is 'Shared team demo store configurations. No per-user store access control yet.';
