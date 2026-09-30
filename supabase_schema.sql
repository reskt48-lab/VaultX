-- ==========================================
-- VAULTX DATABASE
-- ==========================================

create table if not exists public.passwords (
    id uuid primary key default gen_random_uuid(),

    user_id uuid not null
        references auth.users(id)
        on delete cascade,

    website text not null,
    username text not null,

    password_ciphertext text not null,

    notes_ciphertext text,

    image_path text,

    is_favorite boolean not null default false,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);


-- ==========================================
-- ENABLE RLS
-- ==========================================

alter table public.passwords enable row level security;


-- ==========================================
-- SELECT POLICY
-- User hanya bisa melihat data miliknya
-- ==========================================

drop policy if exists "Users can view own passwords"
on public.passwords;

create policy "Users can view own passwords"
on public.passwords
for select
to authenticated
using (
    auth.uid() = user_id
);


-- ==========================================
-- INSERT POLICY
-- ==========================================

drop policy if exists "Users can insert own passwords"
on public.passwords;

create policy "Users can insert own passwords"
on public.passwords
for insert
to authenticated
with check (
    auth.uid() = user_id
);


-- ==========================================
-- UPDATE POLICY
-- ==========================================

drop policy if exists "Users can update own passwords"
on public.passwords;

create policy "Users can update own passwords"
on public.passwords
for update
to authenticated
using (
    auth.uid() = user_id
)
with check (
    auth.uid() = user_id
);


-- ==========================================
-- DELETE POLICY
-- ==========================================

drop policy if exists "Users can delete own passwords"
on public.passwords;

create policy "Users can delete own passwords"
on public.passwords
for delete
to authenticated
using (
    auth.uid() = user_id
);


-- ==========================================
-- UPDATED_AT
-- ==========================================

create or replace function public.update_password_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;


drop trigger if exists passwords_updated_at
on public.passwords;

create trigger passwords_updated_at
before update on public.passwords
for each row
execute function public.update_password_updated_at();


-- ==========================================
-- STORAGE BUCKET
-- ==========================================

insert into storage.buckets (
    id,
    name,
    public
)
values (
    'vault-images',
    'vault-images',
    false
)
on conflict (id) do nothing;


-- ==========================================
-- STORAGE SELECT
-- Path foto:
-- user_id/password_id/filename
-- ==========================================

drop policy if exists "Users can view own vault images"
on storage.objects;

create policy "Users can view own vault images"
on storage.objects
for select
to authenticated
using (
    bucket_id = 'vault-images'
    and (storage.foldername(name))[1] = auth.uid()::text
);


-- ==========================================
-- STORAGE INSERT
-- ==========================================

drop policy if exists "Users can upload own vault images"
on storage.objects;

create policy "Users can upload own vault images"
on storage.objects
for insert
to authenticated
with check (
    bucket_id = 'vault-images'
    and (storage.foldername(name))[1] = auth.uid()::text
);


-- ==========================================
-- STORAGE UPDATE
-- ==========================================

drop policy if exists "Users can update own vault images"
on storage.objects;

create policy "Users can update own vault images"
on storage.objects
for update
to authenticated
using (
    bucket_id = 'vault-images'
    and (storage.foldername(name))[1] = auth.uid()::text
)
with check (
    bucket_id = 'vault-images'
    and (storage.foldername(name))[1] = auth.uid()::text
);


-- ==========================================
-- STORAGE DELETE
-- ==========================================

drop policy if exists "Users can delete own vault images"
on storage.objects;

create policy "Users can delete own vault images"
on storage.objects
for delete
to authenticated
using (
    bucket_id = 'vault-images'
    and (storage.foldername(name))[1] = auth.uid()::text
);