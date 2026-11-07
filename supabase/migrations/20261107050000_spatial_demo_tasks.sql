-- Dedicated hackathon workspace. Browser roles cannot read or write this table.
create table if not exists public.spatial_demo_tasks (
  id uuid primary key,
  workspace_id uuid not null,
  payload jsonb not null,
  revision integer not null default 1,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint bounded_payload check (octet_length(payload::text) < 800000)
);
create index if not exists spatial_demo_tasks_workspace_idx on public.spatial_demo_tasks(workspace_id, created_at desc);
alter table public.spatial_demo_tasks enable row level security;
revoke all on public.spatial_demo_tasks from anon, authenticated;
grant select,insert,update on public.spatial_demo_tasks to service_role;
comment on table public.spatial_demo_tasks is 'Hackathon demo only; Vercel capability session authorizes access. No production store data.';
