-- 作業（指定單元或題目＋期限）與班級總覽。學生完成狀況由學生端同步的摘要（done_ids、track_done）計算。
create table public.assignments (
  id bigserial primary key,
  title text not null check (char_length(title) between 1 and 120),
  track text not null check (track in ('py','cpp','verilog','tcl')),
  units int[] not null default '{}',
  problems text[] not null default '{}',
  due_at timestamptz,
  cohort text not null default '',
  archived boolean not null default false,
  created_at timestamptz not null default now(),
  created_by uuid,
  check (cardinality(units) <= 60 and cardinality(problems) <= 60)
);
alter table public.assignments enable row level security;

-- 是否完成：problems 全在 done_ids 內，且 units 全在 track_done[track] 內
create function public._assign_done(p_a public.assignments, p_summary jsonb) returns boolean language sql immutable set search_path = public, pg_catalog as $$
  select (coalesce(array_length(p_a.units, 1), 0) = 0 or not exists (
            select 1 from unnest(p_a.units) u where not coalesce((p_summary->'track_done'->p_a.track) @> to_jsonb(u), false)))
     and (coalesce(array_length(p_a.problems, 1), 0) = 0 or not exists (
            select 1 from unnest(p_a.problems) q where not coalesce((p_summary->'done_ids') @> to_jsonb(q), false)))
$$;

create function public.admin_assign_save(p_id bigint, p_title text, p_track text, p_units int[], p_problems text[], p_due timestamptz, p_cohort text, p_archived boolean default false)
returns jsonb language plpgsql security definer set search_path = public, pg_catalog as $$
declare v_id bigint;
begin
  perform _need_admin();
  if coalesce(array_length(p_units, 1), 0) + coalesce(array_length(p_problems, 1), 0) = 0 then
    return jsonb_build_object('ok', false, 'reason', 'empty');
  end if;
  if p_id is null then
    insert into assignments(title, track, units, problems, due_at, cohort, archived, created_by)
      values (left(p_title, 120), p_track, coalesce(p_units, '{}'), coalesce(p_problems, '{}'), p_due, left(coalesce(p_cohort, ''), 40), coalesce(p_archived, false), auth.uid()) returning id into v_id;
  else
    update assignments set title = left(p_title, 120), track = p_track, units = coalesce(p_units, '{}'), problems = coalesce(p_problems, '{}'),
      due_at = p_due, cohort = left(coalesce(p_cohort, ''), 40), archived = coalesce(p_archived, false) where id = p_id returning id into v_id;
  end if;
  insert into audit_log(user_id, student_id, action, detail) values (auth.uid(), (select student_id from profiles where id = auth.uid()), 'assign_save', jsonb_build_object('id', v_id, 'title', left(p_title, 120)));
  return jsonb_build_object('ok', v_id is not null, 'id', v_id);
end $$;

create function public.admin_assign_delete(p_id bigint) returns jsonb language plpgsql security definer set search_path = public, pg_catalog as $$
begin
  perform _need_admin();
  delete from assignments where id = p_id;
  insert into audit_log(user_id, student_id, action, detail) values (auth.uid(), (select student_id from profiles where id = auth.uid()), 'assign_delete', jsonb_build_object('id', p_id));
  return jsonb_build_object('ok', true);
end $$;

create function public.admin_assign_list() returns jsonb language plpgsql security definer set search_path = public, pg_catalog as $$
begin
  perform _need_admin();
  return coalesce((select jsonb_agg(jsonb_build_object(
      'id', a.id, 'title', a.title, 'track', a.track, 'units', a.units, 'problems', a.problems, 'due_at', a.due_at, 'cohort', a.cohort, 'archived', a.archived,
      'total', (select count(*) from profiles p where p.role = 'student' and p.active and not p.archived and (a.cohort = '' or a.cohort = p.cohort)),
      'done', (select count(*) from profiles p left join progress g on g.user_id = p.id
               where p.role = 'student' and p.active and not p.archived and (a.cohort = '' or a.cohort = p.cohort) and _assign_done(a, coalesce(g.summary, '{}'))),
      'missing', coalesce((select jsonb_agg(jsonb_build_object('student_id', p.student_id, 'name', p.name) order by p.student_id)
               from profiles p left join progress g on g.user_id = p.id
               where p.role = 'student' and p.active and not p.archived and (a.cohort = '' or a.cohort = p.cohort) and not _assign_done(a, coalesce(g.summary, '{}'))), '[]'::jsonb))
    order by a.archived, a.due_at nulls last, a.id desc) from assignments a), '[]'::jsonb);
end $$;

create function public.my_assignments() returns jsonb language sql stable security definer set search_path = public, pg_catalog as $$
  select coalesce(jsonb_agg(jsonb_build_object('id', a.id, 'title', a.title, 'track', a.track, 'units', a.units, 'problems', a.problems, 'due_at', a.due_at)
         order by a.due_at nulls last, a.id), '[]'::jsonb)
  from assignments a, profiles p where p.id = auth.uid() and p.active and not a.archived and (a.cohort = '' or a.cohort = p.cohort)
$$;

-- 班級總覽：每位學生一列
create function public.admin_class_overview() returns jsonb language plpgsql security definer set search_path = public, pg_catalog as $$
begin
  perform _need_admin();
  return coalesce((select jsonb_agg(jsonb_build_object(
      'student_id', p.student_id, 'name', p.name, 'cohort', p.cohort, 'last_active', g.summary->'last_active',
      'solved', coalesce((g.summary->>'solved')::int, 0), 'active_days', coalesce((g.summary->>'active_days')::int, 0),
      'weekly', coalesce(g.summary->'weekly', '[]'::jsonb), 'stuck', coalesce(g.summary->'stuck', '[]'::jsonb),
      'tracks', coalesce((select jsonb_object_agg(k, jsonb_array_length(v)) from jsonb_each(coalesce(g.summary->'track_done', '{}'::jsonb)) t(k, v)), '{}'::jsonb),
      'overdue', (select count(*) from assignments a where not a.archived and a.due_at is not null and a.due_at < now() and (a.cohort = '' or a.cohort = p.cohort)
                  and not _assign_done(a, coalesce(g.summary, '{}')))
    ) order by p.student_id)
    from profiles p left join progress g on g.user_id = p.id where p.role = 'student' and p.active and not p.archived), '[]'::jsonb);
end $$;

revoke all on function public._assign_done(public.assignments, jsonb), public.admin_assign_save(bigint, text, text, int[], text[], timestamptz, text, boolean), public.admin_assign_delete(bigint),
  public.admin_assign_list(), public.my_assignments(), public.admin_class_overview() from public, anon;
grant execute on function public.admin_assign_save(bigint, text, text, int[], text[], timestamptz, text, boolean), public.admin_assign_delete(bigint),
  public.admin_assign_list(), public.my_assignments(), public.admin_class_overview() to authenticated;
