-- Per-table counts for each run, and a fixed set of statuses.

alter table ops.pipeline_runs add column details jsonb;

alter table ops.pipeline_runs
add constraint pipeline_runs_status_check check (status in ('running', 'succeeded', 'failed'));
