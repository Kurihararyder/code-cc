-- 0004：題目勘誤回報、異常登入偵測、過期自動封存
create table public.reports (id bigserial primary key, at timestamptz not null default now(), user_id uuid references auth.users(id) on delete set null,
  student_id text, problem_id text not null, body text not null, resolved boolean not null default false, resolved_at timestamptz);
alter table public.reports enable row level security;
revoke all on public.reports from anon, authenticated;
revoke all on sequence public.reports_id_seq from anon, authenticated;

create function public.report_problem(p_pid text, p_body text) returns jsonb language plpgsql security definer set search_path = public, pg_catalog as $$
declare r jsonb := access_for(auth.uid(), client_ip());
begin
  if not (r->>'ok')::boolean then return r; end if;
  if length(coalesce(trim(p_body), '')) < 3 or length(p_body) > 2000 or length(coalesce(p_pid, '')) not between 1 and 40 then return jsonb_build_object('ok', false, 'reason', 'bad_input'); end if;
  if (select count(*) from reports where user_id = auth.uid() and at > now() - interval '1 day') >= 20 then return jsonb_build_object('ok', false, 'reason', 'rate_limited'); end if;
  insert into reports(user_id, student_id, problem_id, body) values (auth.uid(), r->>'student_id', trim(p_pid), trim(p_body));
  return jsonb_build_object('ok', true, 'reason', 'ok');
end $$;

create function public.admin_reports(p_resolved boolean default false) returns jsonb language plpgsql security definer set search_path = public, pg_catalog as $$
begin
  perform _need_admin();
  return coalesce((select jsonb_agg(to_jsonb(r) order by r.at desc) from (select * from reports where resolved = p_resolved order by at desc limit 300) r), '[]'::jsonb);
end $$;

create function public.admin_resolve_report(p_id bigint, p boolean) returns void language plpgsql security definer set search_path = public, pg_catalog as $$
begin
  perform _need_admin();
  update reports set resolved = p, resolved_at = case when p then now() else null end where id = p_id;
end $$;

create function public.admin_anomalies() returns jsonb language plpgsql security definer set search_path = public, pg_catalog as $$
begin
  perform _need_admin();
  return jsonb_build_object(
    'multi_ip', coalesce((select jsonb_agg(jsonb_build_object('student_id', student_id, 'ips', n, 'list', l)) from (
        select student_id, count(distinct ip) n, array_agg(distinct ip) l from audit_log where at > now() - interval '1 day' and action = 'login' and ok and ip is not null and student_id is not null
        group by student_id having count(distinct ip) >= 3) t), '[]'::jsonb),
    'denied', coalesce((select jsonb_agg(jsonb_build_object('student_id', student_id, 'n', n)) from (
        select student_id, count(*) n from audit_log where at > now() - interval '1 hour' and not ok and student_id is not null group by student_id having count(*) >= 5) t), '[]'::jsonb),
    'open_reports', (select count(*) from reports where not resolved));
end $$;

create function public.admin_auto_archive(p_days int) returns int language plpgsql security definer set search_path = public, pg_catalog as $$
declare n int;
begin
  perform _need_admin();
  update profiles set archived = true, active = false where role = 'student' and not archived and valid_until is not null and valid_until < now() - make_interval(days => p_days);
  get diagnostics n = row_count;
  insert into audit_log(user_id, student_id, action, detail) values (auth.uid(), (select student_id from profiles where id = auth.uid()), 'admin_archive', jsonb_build_object('auto_days', p_days, 'count', n));
  return n;
end $$;

revoke all on function public.report_problem(text, text), public.admin_reports(boolean), public.admin_resolve_report(bigint, boolean), public.admin_anomalies(), public.admin_auto_archive(int) from public, anon;
grant execute on function public.report_problem(text, text), public.admin_reports(boolean), public.admin_resolve_report(bigint, boolean), public.admin_anomalies(), public.admin_auto_archive(int) to authenticated;
