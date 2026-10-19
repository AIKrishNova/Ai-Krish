-- AI KRISH cloud chat history and settings.
-- Run once: Supabase dashboard > SQL Editor > New query > paste this > Run.
-- Row Level Security means every signed-in user can only ever read or change their own rows.

create table if not exists public.chats (
  user_id    uuid        not null default auth.uid() references auth.users(id) on delete cascade,
  id         text        not null,
  title      text        not null default 'New chat',
  messages   jsonb       not null default '[]'::jsonb,
  updated_at timestamptz not null default now(),
  primary key (user_id, id)
);
create index if not exists chats_user_updated on public.chats (user_id, updated_at desc);

create table if not exists public.user_settings (
  user_id      uuid        primary key default auth.uid() references auth.users(id) on delete cascade,
  instructions text        not null default '',
  notes        jsonb       not null default '[]'::jsonb,
  done         jsonb       not null default '[]'::jsonb,
  updated_at   timestamptz not null default now()
);

alter table public.chats         enable row level security;
alter table public.user_settings enable row level security;

drop policy if exists "own chats"    on public.chats;
drop policy if exists "own settings" on public.user_settings;

create policy "own chats" on public.chats
  for all to authenticated
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "own settings" on public.user_settings
  for all to authenticated
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Nobody who is signed out can touch these tables.
revoke all on public.chats, public.user_settings from anon;
