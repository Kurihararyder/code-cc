-- 靜宜大學晶片設計學士學位學程 CPE 練功系統：資料庫結構
create extension if not exists pgcrypto with schema extensions;

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  student_id text not null unique,
  name text not null default '',
  role text not null default 'student' check (role in ('student','admin')),
  cohort text not null default '',
  active boolean not null default false,
  valid_from timestamptz, valid_until timestamptz,
  ai_allowed boolean not null default false,
  ip_mode text not null default 'inherit' check (ip_mode in ('inherit','any','list')),
  allowed_ips text[] not null default '{}',
  must_change_pw boolean not null default true,
  note text not null default '',
  last_login_at timestamptz, last_ip text, login_count int not null default 0,
  created_at timestamptz not null default now()
);
create table public.app_settings (key text primary key, value jsonb not null, updated_at timestamptz not null default now());
create table public.app_secrets (key text primary key, value text not null, updated_at timestamptz not null default now());
create table public.progress (user_id uuid primary key references auth.users(id) on delete cascade,
  data jsonb not null default '{}', summary jsonb not null default '{}', device text, updated_at timestamptz not null default now());
create table public.audit_log (id bigserial primary key, at timestamptz not null default now(), user_id uuid, student_id text,
  action text not null, ip text, ok boolean not null default true, detail jsonb);
create index on public.audit_log (at desc);
create table public.ai_usage (id bigserial primary key, at timestamptz not null default now(), user_id uuid, student_id text,
  model text, tokens_in int not null default 0, tokens_out int not null default 0);
create index on public.ai_usage (user_id, at desc);

alter table public.profiles enable row level security;
alter table public.app_settings enable row level security;
alter table public.app_secrets enable row level security;
alter table public.progress enable row level security;
alter table public.audit_log enable row level security;
alter table public.ai_usage enable row level security;
revoke all on public.profiles, public.app_settings, public.app_secrets, public.progress, public.audit_log, public.ai_usage from anon, authenticated;
revoke all on sequence public.audit_log_id_seq, public.ai_usage_id_seq from anon, authenticated;
-- 唯一可直接讀的：自己的 profile（RLS 限制）
grant select on public.profiles to authenticated;
create policy own_profile on public.profiles for select to authenticated using (id = auth.uid());

insert into public.app_settings(key, value) values
 ('ip_policy', '{"enabled": false, "cidrs": []}'),
 ('ai', '{"enabled": false, "model": "gpt-4o", "daily_calls": 60, "max_tokens": 1500}'),
 ('app', '{"latest_version": "2.9.0", "min_version": "2.9.0", "announcement": "", "update_note": ""}'),
 ('offline', '{"grace_hours": 72}');

-- 只允許管理員建立的帳號（擋掉任何人用公開金鑰自行註冊）
create function public.block_self_signup() returns trigger language plpgsql as $$
begin
  if coalesce(new.raw_app_meta_data->>'provisioned','') <> 'true' then raise exception 'signup disabled'; end if;
  return new;
end $$;
create trigger block_self_signup before insert on auth.users for each row execute function public.block_self_signup();

-- 修正（0003）：GoTrue 建立使用者時 app_metadata 是『事後更新』，所以改用短暫開啟的閘門：只有管理員的 Edge Function 建立帳號期間才允許新增
create table public.signup_gate (id int primary key default 1 check (id = 1), open_until timestamptz not null default now());
insert into public.signup_gate default values;
alter table public.signup_gate enable row level security;
revoke all on public.signup_gate from anon, authenticated;
create or replace function public.block_self_signup() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if not exists (select 1 from public.signup_gate where open_until > now()) then raise exception 'signup disabled'; end if;
  return new;
end $$;
revoke all on function public.block_self_signup() from public, anon, authenticated;
