-- 0003：封存、分班公告、到期清單、學習分析、完整匯出
alter table public.profiles add column archived boolean not null default false;
insert into public.app_settings(key, value) values ('notices', '{"items": []}') on conflict do nothing;

create function public.admin_set_archived(p_ids uuid[], p boolean) returns int language plpgsql security definer set search_path = public, pg_catalog as $$
declare n int;
begin
  perform _need_admin();
  update profiles set archived = p, active = case when p then false else active end where id = any(p_ids) and id <> auth.uid() and role = 'student';
  get diagnostics n = row_count;
  insert into audit_log(user_id, student_id, action, detail) values (auth.uid(), (select student_id from profiles where id = auth.uid()), 'admin_archive', jsonb_build_object('count', n, 'archived', p));
  return n;
end $$;

-- items: [{id, text, cohort(空=全部), from, until}]
create function public.admin_set_notices(p jsonb) returns void language plpgsql security definer set search_path = public, pg_catalog as $$
begin
  perform _need_admin();
  if jsonb_typeof(p->'items') <> 'array' then raise exception '格式錯誤'; end if;
  insert into app_settings(key, value, updated_at) values ('notices', p, now()) on conflict (key) do update set value = excluded.value, updated_at = now();
  insert into audit_log(user_id, student_id, action, detail) values (auth.uid(), (select student_id from profiles where id = auth.uid()), 'admin_setting', jsonb_build_object('key', 'notices'));
end $$;

create function public.my_notices() returns jsonb language sql stable security definer set search_path = public, pg_catalog as $$
  select coalesce(jsonb_agg(i), '[]'::jsonb) from app_settings s, jsonb_array_elements(s.value->'items') i, profiles p
  where s.key = 'notices' and p.id = auth.uid()
    and (coalesce(i->>'cohort', '') = '' or i->>'cohort' = p.cohort)
    and (coalesce(i->>'from', '') = '' or (i->>'from')::timestamptz <= now())
    and (coalesce(i->>'until', '') = '' or (i->>'until')::timestamptz >= now()) $$;

create function public.admin_expiring(p_days int default 14) returns jsonb language plpgsql security definer set search_path = public, pg_catalog as $$
begin
  perform _need_admin();
  return coalesce((select jsonb_agg(jsonb_build_object('id', id, 'student_id', student_id, 'name', name, 'cohort', cohort, 'valid_until', valid_until) order by valid_until)
    from profiles where role = 'student' and active and not archived and valid_until between now() - interval '30 days' and now() + make_interval(days => p_days)), '[]'::jsonb);
end $$;

create function public.admin_insights() returns jsonb language plpgsql security definer set search_path = public, pg_catalog as $$
begin
  perform _need_admin();
  return jsonb_build_object(
    'stuck', coalesce((select jsonb_agg(r order by (r->>'students')::int desc, (r->>'attempts')::int desc) from (
        select jsonb_build_object('id', s->>'id', 'students', count(*), 'attempts', sum((s->>'attempts')::int)) r
        from progress g join profiles p on p.id = g.user_id and p.active and not p.archived, jsonb_array_elements(coalesce(g.summary->'stuck', '[]'::jsonb)) s
        group by s->>'id' order by count(*) desc, sum((s->>'attempts')::int) desc limit 15) t), '[]'::jsonb),
    'inactive', coalesce((select jsonb_agg(jsonb_build_object('student_id', p.student_id, 'name', p.name, 'cohort', p.cohort, 'last_active', g.summary->'last_active', 'last_login', p.last_login_at) order by p.student_id)
        from profiles p left join progress g on g.user_id = p.id
        where p.role = 'student' and p.active and not p.archived
          and (g.summary->>'last_active' is null or to_timestamp((g.summary->>'last_active')::double precision) < now() - interval '14 days')), '[]'::jsonb),
    'units', coalesce((select jsonb_agg(jsonb_build_object('unit', u, 'n', n) order by u) from (
        select (g.summary->>'unit')::int u, count(*) n from progress g join profiles p on p.id = g.user_id and p.active and not p.archived group by 1) t), '[]'::jsonb),
    'weekly', coalesce((select jsonb_agg(jsonb_build_object('week_ago', 3 - (i - 1), 'active', (select count(*) from progress g join profiles p on p.id = g.user_id and p.active and not p.archived
        where coalesce((g.summary->'weekly'->>(i - 1))::int, 0) > 0)) order by i) from generate_series(1, 4) i), '[]'::jsonb),
    'solved_avg', (select coalesce(round(avg((g.summary->>'solved')::numeric), 1), 0) from progress g join profiles p on p.id = g.user_id and p.active and not p.archived));
end $$;

create function public.admin_export() returns jsonb language plpgsql security definer set search_path = public, pg_catalog as $$
begin
  perform _need_admin();
  insert into audit_log(user_id, student_id, action) values (auth.uid(), (select student_id from profiles where id = auth.uid()), 'admin_export');
  return jsonb_build_object('exported_at', now(), 'format', 1,
    'profiles', (select coalesce(jsonb_agg(to_jsonb(p)), '[]') from profiles p),
    'settings', (select coalesce(jsonb_object_agg(key, value), '{}') from app_settings),
    'progress', (select coalesce(jsonb_agg(jsonb_build_object('user_id', user_id, 'summary', summary, 'updated_at', updated_at, 'data', data)), '[]') from progress),
    'audit', (select coalesce(jsonb_agg(to_jsonb(a)), '[]') from (select * from audit_log order by at desc limit 2000) a));
end $$;

revoke all on function public.admin_set_archived(uuid[], boolean), public.admin_set_notices(jsonb), public.my_notices(), public.admin_expiring(int), public.admin_insights(), public.admin_export() from public, anon;
grant execute on function public.admin_set_archived(uuid[], boolean), public.admin_set_notices(jsonb), public.my_notices(), public.admin_expiring(int), public.admin_insights(), public.admin_export() to authenticated;
