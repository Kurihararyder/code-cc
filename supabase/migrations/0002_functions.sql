create function public.is_admin() returns boolean language sql stable security definer set search_path = public as $$
  select exists(select 1 from profiles where id = auth.uid() and role = 'admin' and active) $$;

create function public.client_ip() returns inet language plpgsql stable as $$
declare h json; x text;
begin
  begin h := current_setting('request.headers', true)::json; exception when others then return null; end;
  if h is null then return null; end if;
  x := coalesce(nullif(h->>'cf-connecting-ip',''), split_part(h->>'x-forwarded-for', ',', 1));
  begin return trim(x)::inet; exception when others then return null; end;
end $$;

create function public.app_info() returns jsonb language sql stable security definer set search_path = public as $$
  select coalesce((select value from app_settings where key='app'), '{}'::jsonb)
         || jsonb_build_object('grace_hours', coalesce((select (value->>'grace_hours')::int from app_settings where key='offline'), 72),
                               'ai_enabled', coalesce((select (value->>'enabled')::boolean from app_settings where key='ai'), false)) $$;

create function public.access_for(p_uid uuid, p_ip inet) returns jsonb language plpgsql security definer set search_path = public as $$
declare p profiles; pol jsonb; reason text := 'ok'; lst text[]; hit boolean;
begin
  select * into p from profiles where id = p_uid;
  if not found then return jsonb_build_object('ok', false, 'reason', 'no_profile'); end if;
  if not p.active then reason := 'inactive';
  elsif p.valid_from is not null and now() < p.valid_from then reason := 'not_started';
  elsif p.valid_until is not null and now() > p.valid_until then reason := 'expired';
  elsif p.role <> 'admin' then
    if p.ip_mode = 'list' then lst := p.allowed_ips;
    elsif p.ip_mode = 'inherit' then
      select value into pol from app_settings where key = 'ip_policy';
      if coalesce((pol->>'enabled')::boolean, false) then lst := array(select jsonb_array_elements_text(pol->'cidrs')); end if;
    end if;
    if lst is not null then
      if p_ip is null then reason := 'ip_unknown';
      else
        select exists(select 1 from unnest(lst) c where p_ip <<= c::inet) into hit;
        if not hit then reason := 'ip_denied'; end if;
      end if;
    end if;
  end if;
  return jsonb_build_object('ok', reason = 'ok', 'reason', reason, 'role', p.role, 'student_id', p.student_id, 'name', p.name,
    'cohort', p.cohort, 'valid_from', p.valid_from, 'valid_until', p.valid_until, 'ai_allowed', p.ai_allowed,
    'must_change_pw', p.must_change_pw, 'ip', host(p_ip), 'server_time', now());
end $$;

create function public.check_access(p_login boolean default false) returns jsonb language plpgsql security definer set search_path = public as $$
declare r jsonb; v_ip inet := client_ip(); v_sid text;
begin
  if auth.uid() is null then return jsonb_build_object('ok', false, 'reason', 'no_session'); end if;
  r := access_for(auth.uid(), v_ip);
  v_sid := r->>'student_id';
  if p_login or not (r->>'ok')::boolean then
    insert into audit_log(user_id, student_id, action, ip, ok, detail) values (auth.uid(), v_sid, case when p_login then 'login' else 'check' end, host(v_ip), (r->>'ok')::boolean, jsonb_build_object('reason', r->>'reason'));
  end if;
  if p_login and (r->>'ok')::boolean then
    update profiles set last_login_at = now(), last_ip = host(v_ip), login_count = login_count + 1 where id = auth.uid();
  end if;
  return r || jsonb_build_object('app', app_info());
end $$;

create function public.pw_changed() returns void language sql security definer set search_path = public as $$
  update profiles set must_change_pw = false where id = auth.uid() $$;

create function public.save_progress(p_data jsonb, p_summary jsonb, p_device text) returns jsonb language plpgsql security definer set search_path = public as $$
declare r jsonb := access_for(auth.uid(), client_ip());
begin
  if not (r->>'ok')::boolean then return r; end if;
  if length(p_data::text) > 12000000 then return jsonb_build_object('ok', false, 'reason', 'too_large'); end if;
  insert into progress(user_id, data, summary, device, updated_at) values (auth.uid(), p_data, coalesce(p_summary,'{}'), p_device, now())
  on conflict (user_id) do update set data = excluded.data, summary = excluded.summary, device = excluded.device, updated_at = now();
  return jsonb_build_object('ok', true, 'reason', 'ok', 'saved_at', now());
end $$;

create function public.load_progress() returns jsonb language plpgsql security definer set search_path = public as $$
declare r jsonb := access_for(auth.uid(), client_ip()); g progress;
begin
  if not (r->>'ok')::boolean then return r; end if;
  select * into g from progress where user_id = auth.uid();
  if not found then return jsonb_build_object('ok', true, 'reason', 'ok', 'data', null); end if;
  return jsonb_build_object('ok', true, 'reason', 'ok', 'data', g.data, 'updated_at', g.updated_at, 'device', g.device);
end $$;

-- ---------- 管理員 ----------
create function public._need_admin() returns void language plpgsql stable as $$
begin if not public.is_admin() then raise exception 'admin only' using errcode = '42501'; end if; end $$;

create function public.admin_list_users() returns jsonb language plpgsql security definer set search_path = public as $$
begin
  perform _need_admin();
  return coalesce((select jsonb_agg(to_jsonb(p) - 'id' || jsonb_build_object('id', p.id, 'progress_at', g.updated_at, 'summary', coalesce(g.summary,'{}'),
      'ai_calls_24h', (select count(*) from ai_usage u where u.user_id = p.id and u.at > now() - interval '1 day'),
      'status', replace(access_for(p.id, null)->>'reason', 'ip_unknown', 'ok'))
      order by p.role, p.student_id)
    from profiles p left join progress g on g.user_id = p.id), '[]'::jsonb);
end $$;

create function public.admin_update_user(p_id uuid, p jsonb) returns void language plpgsql security definer set search_path = public as $$
declare k text; cidr text;
begin
  perform _need_admin();
  if p_id = auth.uid() and (p ? 'role' or p ? 'active') then raise exception '不能更改自己的角色或啟用狀態'; end if;
  if p ? 'allowed_ips' then
    for cidr in select jsonb_array_elements_text(p->'allowed_ips') loop
      begin perform cidr::inet; exception when others then raise exception 'IP 格式錯誤：%', cidr; end;
    end loop;
  end if;
  update profiles set
    name = coalesce(p->>'name', name), cohort = coalesce(p->>'cohort', cohort), note = coalesce(p->>'note', note),
    role = coalesce(p->>'role', role), active = coalesce((p->>'active')::boolean, active),
    ai_allowed = coalesce((p->>'ai_allowed')::boolean, ai_allowed), must_change_pw = coalesce((p->>'must_change_pw')::boolean, must_change_pw),
    ip_mode = coalesce(p->>'ip_mode', ip_mode),
    allowed_ips = case when p ? 'allowed_ips' then array(select jsonb_array_elements_text(p->'allowed_ips')) else allowed_ips end,
    valid_from = case when p ? 'valid_from' then nullif(p->>'valid_from','')::timestamptz else valid_from end,
    valid_until = case when p ? 'valid_until' then nullif(p->>'valid_until','')::timestamptz else valid_until end
  where id = p_id;
  insert into audit_log(user_id, student_id, action, detail) values (auth.uid(), (select student_id from profiles where id = auth.uid()), 'admin_update', jsonb_build_object('target', p_id, 'patch', p));
end $$;

create function public.admin_bulk_update(p_ids uuid[], p jsonb) returns int language plpgsql security definer set search_path = public as $$
declare i uuid; n int := 0;
begin
  perform _need_admin();
  foreach i in array p_ids loop
    if i <> auth.uid() then perform admin_update_user(i, p); n := n + 1; end if;
  end loop;
  return n;
end $$;

create function public.admin_get_settings() returns jsonb language plpgsql security definer set search_path = public as $$
begin perform _need_admin(); return (select jsonb_object_agg(key, value) from app_settings); end $$;

create function public.admin_set_setting(p_key text, p_value jsonb) returns void language plpgsql security definer set search_path = public as $$
declare cidr text;
begin
  perform _need_admin();
  if p_key not in ('ip_policy','ai','app','offline') then raise exception '不認得的設定：%', p_key; end if;
  if p_key = 'ip_policy' then
    for cidr in select jsonb_array_elements_text(p_value->'cidrs') loop
      begin perform cidr::inet; exception when others then raise exception 'IP 格式錯誤：%', cidr; end;
    end loop;
  end if;
  insert into app_settings(key, value, updated_at) values (p_key, p_value, now()) on conflict (key) do update set value = excluded.value, updated_at = now();
  insert into audit_log(user_id, student_id, action, detail) values (auth.uid(), (select student_id from profiles where id = auth.uid()), 'admin_setting', jsonb_build_object('key', p_key, 'value', p_value));
end $$;

create function public.admin_secret_status() returns jsonb language plpgsql security definer set search_path = public as $$
begin
  perform _need_admin();
  return coalesce((select jsonb_build_object('set', true, 'last4', right(value, 4), 'updated_at', updated_at) from app_secrets where key = 'openai_key'), jsonb_build_object('set', false));
end $$;

create function public.admin_set_secret(p_value text) returns void language plpgsql security definer set search_path = public as $$
begin
  perform _need_admin();
  if coalesce(trim(p_value), '') = '' then delete from app_secrets where key = 'openai_key';
  else insert into app_secrets(key, value, updated_at) values ('openai_key', trim(p_value), now()) on conflict (key) do update set value = excluded.value, updated_at = now(); end if;
  insert into audit_log(user_id, student_id, action, detail) values (auth.uid(), (select student_id from profiles where id = auth.uid()), 'admin_secret', jsonb_build_object('cleared', coalesce(trim(p_value), '') = ''));
end $$;

create function public.admin_audit(p_limit int default 100, p_offset int default 0, p_student text default null, p_action text default null) returns jsonb language plpgsql security definer set search_path = public as $$
begin
  perform _need_admin();
  return coalesce((select jsonb_agg(to_jsonb(a) order by a.at desc) from (select * from audit_log
     where (p_student is null or student_id = p_student) and (p_action is null or action = p_action)
     order by at desc limit least(p_limit, 500) offset p_offset) a), '[]'::jsonb);
end $$;

create function public.admin_overview() returns jsonb language plpgsql security definer set search_path = public as $$
begin
  perform _need_admin();
  return jsonb_build_object(
    'students', (select count(*) from profiles where role = 'student'),
    'active', (select count(*) from profiles where role = 'student' and active and (valid_until is null or valid_until > now()) and (valid_from is null or valid_from <= now())),
    'pending', (select count(*) from profiles where role = 'student' and not active),
    'expired', (select count(*) from profiles where role = 'student' and valid_until < now()),
    'ai_allowed', (select count(*) from profiles where role = 'student' and ai_allowed),
    'logins_24h', (select count(*) from audit_log where action = 'login' and ok and at > now() - interval '1 day'),
    'denied_24h', (select count(*) from audit_log where not ok and at > now() - interval '1 day'),
    'ai_calls_24h', (select count(*) from ai_usage where at > now() - interval '1 day'),
    'ai_tokens_7d', (select coalesce(sum(tokens_in + tokens_out), 0) from ai_usage where at > now() - interval '7 days'),
    'expiring_7d', (select count(*) from profiles where role = 'student' and valid_until between now() and now() + interval '7 days'),
    'cohorts', coalesce((select jsonb_agg(jsonb_build_object('cohort', c, 'n', n)) from (select cohort c, count(*) n from profiles where role = 'student' group by cohort order by cohort) t), '[]'::jsonb));
end $$;

create function public.admin_ai_usage(p_days int default 7) returns jsonb language plpgsql security definer set search_path = public as $$
begin
  perform _need_admin();
  return coalesce((select jsonb_agg(r order by r->>'student_id') from (select jsonb_build_object('student_id', student_id, 'calls', count(*), 'tokens_in', sum(tokens_in), 'tokens_out', sum(tokens_out), 'last', max(at)) r
     from ai_usage where at > now() - make_interval(days => p_days) group by student_id) t), '[]'::jsonb);
end $$;

-- 權限：預設 public 與 anon 都能執行函式，這裡全部收回再逐一開放
do $$ declare f record; begin
  for f in select p.oid::regprocedure as sig from pg_proc p join pg_namespace n on n.oid = p.pronamespace where n.nspname = 'public' loop
    execute format('revoke all on function %s from public, anon, authenticated', f.sig);
  end loop;
end $$;
grant execute on function public.app_info() to anon, authenticated;
grant execute on function public.check_access(boolean), public.pw_changed(), public.save_progress(jsonb, jsonb, text), public.load_progress(),
  public.admin_list_users(), public.admin_update_user(uuid, jsonb), public.admin_bulk_update(uuid[], jsonb), public.admin_get_settings(),
  public.admin_set_setting(text, jsonb), public.admin_secret_status(), public.admin_set_secret(text), public.admin_audit(int, int, text, text),
  public.admin_overview(), public.admin_ai_usage(int) to authenticated;
grant execute on function public.is_admin(), public.client_ip(), public._need_admin() to authenticated;
grant execute on function public.access_for(uuid, inet) to service_role;

-- 0004：兩個輔助函式固定 search_path
alter function public.client_ip() set search_path = public, pg_catalog;
alter function public._need_admin() set search_path = public, pg_catalog;
