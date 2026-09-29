create table if not exists companies (
    company_number text primary key,
    company_name text,
    sic_codes jsonb,
    date_of_incorporation date,
    company_status text,
    profile jsonb,
    last_enriched_at timestamptz,
    updated_at timestamptz default now()
);

create table if not exists stream_events (
    id bigint generated always as identity primary key,
    stream_name text not null,
    company_number text,
    resource_id text,
    event_type text,
    fields_changed jsonb,
    published_at timestamptz,
    timepoint bigint,
    raw_payload jsonb not null,
    processed_at timestamptz,
    created_at timestamptz default now(),
    unique(stream_name, resource_id, timepoint)
);

create table if not exists filings (
    company_number text not null,
    transaction_id text not null,
    form_type text,
    description text,
    filing_date date,
    action_date date,
    document_url text,
    raw_payload jsonb,
    created_at timestamptz default now(),
    primary key(company_number, transaction_id)
);

create table if not exists psc_records (
    company_number text not null,
    resource_id text not null,
    name text,
    entity_type text,
    nature_of_control jsonb,
    notified_on date,
    ceased_on date,
    active boolean default true,
    raw_payload jsonb,
    updated_at timestamptz default now(),
    primary key(company_number, resource_id)
);

create table if not exists screening_events (
    id bigint generated always as identity primary key,
    company_number text not null,
    company_name text,
    nature_of_change text not null,
    new_psc_name text,
    sic_codes jsonb,
    date_of_incorporation date,
    sh01_date date,
    psc_date date,
    confidence_score integer default 0,
    explanation text,
    detected_at timestamptz default now(),
    reviewed boolean default false,
    unique(company_number, nature_of_change, sh01_date, psc_date)
);

create table if not exists stream_checkpoints (
    stream_name text primary key,
    timepoint bigint not null,
    updated_at timestamptz default now()
);

create index if not exists idx_screening_detected_at on screening_events(detected_at desc);
create index if not exists idx_screening_company on screening_events(company_number);
create index if not exists idx_filings_form_type on filings(form_type);
create index if not exists idx_stream_events_company on stream_events(company_number);
