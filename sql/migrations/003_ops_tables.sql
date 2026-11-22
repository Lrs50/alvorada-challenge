-- ops: one row per pipeline run, and the rows a run rejected.

create schema if not exists ops;

create table ops.pipeline_runs (
    run_id serial primary key,
    started_at timestamptz not null default now(),
    finished_at timestamptz,
    status text not null default 'running',
    rows_read integer,
    rows_loaded integer,
    rows_rejected integer,
    error text
);

create table ops.reject (
    run_id integer not null references ops.pipeline_runs,
    source_table text not null,
    row_data jsonb not null,
    reason text not null
);
