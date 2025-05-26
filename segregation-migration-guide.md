### Wildlife Licensing Segregation Migration Guide

**Step 1: Export Wildlife Licensing tables and data.**

Dump base tables and data required fo Wildlife Licensing

```
pg_dump -U ledger_user_name -W --exclude-table='django_cron*' -t 'wl_*' -t 'django_*' -t 'auth_*' -t 'basket_*' -t 'accounts_*' -t 'address_*' -t 'catalogue_*' -t 'partner_*' -t 'licence_*' -t 'social_auth_*' -t 'customer_*' -t 'voucher_*' -t 'payments_*' -t 'promotions_*'  -t 'offer_*' -t 'order_*' ledger_database_name -h ledger_database_host > wl_ledger_tables.sql
```

Dump only the reversion table schema (will assess this data at a later date)

```
pg_dump --schema-only -U ledger_user_name -W  -t 'reversion_*' ledger_database_name -h ledger_database_host > reversion_schema_wl_ledger_tables.sql
```

**Step 2: Import Data into newly created database**

Import base data and tables for Wildlife Licensing.

```
psql "host=wls_database_host port=5432 dbname=wls_database_name user=wls_user_name" < wl_ledger_tables.sql
```

Change table names for m2m relationships so they don't conflict with new local names:

ALTER TABLE wl_applications_application_documents
RENAME TO wl_applications_application_documents_old;

ALTER TABLE wl_main_communicationslogentry_documents
RENAME TO wl_main_communicationslogentry_documents_old;

<!-- For this one we will keep the old data but the table needs to be renamed -->

CREATE TABLE wl_main_assessorgroupmembers AS TABLE wl_main_assessorgroup_members;

Import Base schema for reversion.

```
psql "host=wls_database_host port=5432 dbname=wls_database_name user=wls_user_name" < reversion_schema_wl_ledger_tables.sql
```

**Step 3: Fix and Apply migrations**

a) Create copy of table:

```
CREATE TABLE django_migrations_temp AS SELECT * from django_migrations;

```

b). Delete Migrations in order to apply ledger_api_client migration

```
delete from django_migrations where id > 11;
```

c). Run ledger_api_client migrations

```
python manage.py migrate ledger_api_client
```

d). Reinsert the migrations that were deleted in step 3b.

```
insert into django_migrations (id,app,name,applied) select * from  django_migrations_temp  where id > 11;
```

e). Delete django cron migrations so they can be created from initial migration.

```
delete from django_migrations where app = 'django_cron';
```

f). Apply the migrations up to the point the local document is created
(we need to migrate the data in step 4 below before continuing
because at some point we will remove ledger accounts document model/data from the project
entirely at which point the table will be dropped.)

```
python manage.py migrate wl_main 0026_auto_20250210_1538
```

**Step 4: Copy LocalDocument Data from ledger to local system**

INSERT INTO wl_main_document select \* from accounts_document;

**Step 5: Migrate forward to when all the new m2m fields to the new Document model have been created then copy in the data from the old tables:**

./manage.py migrate wl_main 0028_auto_20250211_1235

INSERT INTO wl_applications_application_documents select \* from wl_applications_application_documents_old;

INSERT INTO wl_main_communicationslogentry_documents select \* from wl_main_communicationslogentry_documents_old;

**Step 6: Copy data from old licence type and licence tables to new tables**

INSERT INTO wl_main_licencetype (id, effective_to, name, short_name, version, code, act, statement, authority, is_renewable, keywords, replaced_by_id) select id, effective_to, name, short_name, version, code, act, statement, authority, is_renewable, keywords, replaced_by_id from licence_licencetype;

INSERT INTO wl_main_licence (id, effective_to, licence_number, licence_sequence, issue_date, start_date, end_date, is_renewable, holder_id, issuer_id, licence_type_id
) select id, effective_to, licence_number, licence_sequence, issue_date, start_date, end_date, is_renewable, holder_id, issuer_id, licence_type_id
from licence_licence;

To Do: During a real environment transfer we must copy the actual files

Migrate to wl_main 0037_rename_user_id_address_user (so that all these new models are created)

**Step 7: Copy Data from the ledger / oscar models into wild lice versions:**

Country

INSERT INTO wl_main_country (iso_3166_1_a2, iso_3166_1_a3, iso_3166_1_numeric, printable_name, name, display_order, is_shipping_country) SELECT iso_3166_1_a2, iso_3166_1_a3, iso_3166_1_numeric, printable_name, name, display_order, is_shipping_country FROM address_country;

UserAddress

INSERT INTO wl_main_useraddress (id, title, first_name, last_name, line1, line2, line3, line4, state, postcode, search_text, phone_number, notes, is_default_for_shipping, is_default_for_billing, hash, date_created, country_id, user_id, num_orders_as_billing_address, num_orders_as_shipping_address) SELECT id, title, first_name, last_name, line1, line2, line3, line4, state, postcode, search_text, phone_number, notes, is_default_for_shipping, is_default_for_billing, hash, date_created, country_id, user_id, num_orders_as_billing_address, num_orders_as_shipping_address FROM address_useraddress;

Address

INSERT INTO wl_main_address (id, line1, line2, line3, locality, state, country, postcode, search_text, hash, oscar_address_id, user_id) SELECT id, line1, line2, line3, locality, state, country, postcode, search_text, hash, oscar_address_id, user_id FROM accounts_address;

Profile

INSERT INTO wl_main_profile (id, name, email, institution, postal_address_id, user_id) SELECT id, name, email, institution, postal_address_id, user_id FROM accounts_profile;

EmailIdentity

INSERT INTO wl_main_emailidentity (id, email, user_id) SELECT id, email, user_id FROM accounts_emailidentity;

**Step 8: Continue with applying migrations ./manage.py migrate**

For error "relation "wl_main_assessorgroup_members" already exists" fake that migration (./manage.py migrate --fake wl_main 0039).

**Step 9: Make sure the auto id sequences are correct in any postgres tables we have manually added data to.**

./manage.py sqlsequencereset wl_applications wl_main

Then run the resulting SQL either in django dbshell or directly in postgres psql

You will get an error that wl_main_assessorgroup_members doesn't exist as it is removed in a migration so create it by copying
from the one we created earlier.

CREATE TABLE wl_main_assessorgroup_members AS TABLE wl_main_assessorgroupmembers;

**Step 10: Drop any constraints linking wildlife licencing tables to ledger tables**

This is due to a hack that was used to alter foreign keys without losing data (by changing the field name and
altering the field in the same migration). Apologies that there are so many of these. It wasn't realised at
the time that it would create this much manual work.

(Unfortunately the name of constraints may vary as they may have been abbreviated by a different version of django/postgres so you will have to check their names manually with psql)

1. wl_main_wildlifelicence:

- Constraint for foreign key linking wl_main_wildlifelicence to licence_licence

ALTER TABLE wl_main_wildlifelicence
DROP CONSTRAINT wl_main_wildlifel_licence_ptr_id_86d7b457_fk_licence_licence_id;

- Constraint for foreign key linking wl_main_wildlifelicence to accounts_profile

ALTER TABLE wl_main_wildlifelicence
DROP CONSTRAINT wl_main_wildlifelice_profile_id_9f39729c_fk_accounts_profile_id;

- Constraint for foreign key linking wl_main_wildlifelicence to accounts_document

ALTER TABLE wl_main_wildlifelicence
DROP CONSTRAINT wl_ma_cover_letter_document_id_a8274c8e_fk_accounts_document_id;

ALTER TABLE wl_main_wildlifelicence
DROP CONSTRAINT wl_main_wi_licence_document_id_65f07e8c_fk_accounts_document_id;

2. wl_main_wildlifelicencetype:

- Constraint for foreign key linking wl_main_wildlifelicencetype to licence_licencetype;

ALTER TABLE wl_main_wildlifelicencetype
DROP CONSTRAINT wl_main_w_licencetype_ptr_id_18098823_fk_licence_licencetype_id;

3. wl_applications_application:

- Constraint for foreign key linking wl_applications_application to accounts_profile;

ALTER TABLE wl_applications_application
DROP CONSTRAINT wl_applica_applicant_profile_id_24373d6c_fk_accounts_profile_id;

- Constraint for foreign key linking wl_applications_application to accounts_document;

ALTER TABLE wl_applications_application
DROP CONSTRAINT wl_applications_a_hard_copy_id_8c41f362_fk_accounts_document_id;

- Delete any constraints to accounts_emailuser since those field are now linked to
  the unmanaged model EmailUserRO:

The fastest way to do this would be to drop the accounts_emailuser table from the wildlife licensing
database and cascade constraints.

DROP TABLE accounts_emailuser CASCADE;

However it can also be done manually using the following query to find the constraints without having to drop the table:

```
SELECT
    conname AS constraint_name,
    conrelid::regclass AS table_name,
    confrelid::regclass AS referenced_table,
    pg_get_constraintdef(oid) AS definition
FROM
    pg_constraint
WHERE
    contype = 'f'
    AND confrelid = 'accounts_emailuser'::regclass
    AND conrelid::regclass::text LIKE '%wl_%';
```

```
ALTER TABLE wl_applications_application
DROP CONSTRAINT wl_applic_assigned_officer_id_1ba6f1d5_fk_accounts_emailuser_id;

ALTER TABLE wl_applications_application
DROP CONSTRAINT wl_applica_proxy_applicant_id_6338d187_fk_accounts_emailuser_id;

ALTER TABLE wl_applications_application
DROP CONSTRAINT wl_applications_appl_applicant_id_6e1a0480_fk_accounts_;

ALTER TABLE wl_applications_assessment
DROP CONSTRAINT wl_appli_assigned_assessor_id_e6a39909_fk_accounts_emailuser_id;

ALTER TABLE wl_applications_applicationrequest
DROP CONSTRAINT wl_applications_ap_officer_id_771456d0_fk_accounts_emailuser_id;

ALTER TABLE wl_applications_applicationdeclineddetails
DROP CONSTRAINT wl_applications_ap_officer_id_79574921_fk_accounts_emailuser_id;

ALTER TABLE wl_applications_applicationuseraction
DROP CONSTRAINT wl_applications_applic_who_id_9f71daf0_fk_accounts_emailuser_id;

ALTER TABLE wl_main_assessorgroup_members_old
DROP CONSTRAINT wl_main_assessor_emailuser_id_d8686176_fk_accounts_emailuser_id;

ALTER TABLE wl_ main_communicationslogentry
DROP CONSTRAINT wl_main_communicatio_customer_id_f9528a2a_fk_accounts_;

ALTER TABLE wl_main_communicationslogentry
DROP CONSTRAINT wl_main_communicatio_staff_id_410a161a_fk_accounts_emailuser_id;

ALTER TABLE wl_returns_return
DROP CONSTRAINT wl_returns__proxy_customer_id_b8485a01_fk_accounts_emailuser_id;

ALTER TABLE wl_returns_returnamendmentrequest
DROP CONSTRAINT wl_returns_returna_officer_id_0d7702ea_fk_accounts_emailuser_id;

ALTER TABLE wl_main_useraddress
DROP CONSTRAINT wl_main_useraddress_user_id_25f3218a_fk_accounts_emailuser_id;

ALTER TABLE wl_main_emailidentity
DROP CONSTRAINT wl_main_emailidentity_user_id_fe61093c_fk_accounts_emailuser_id;

ALTER TABLE wl_main_profile
DROP CONSTRAINT wl_main_profile_user_id_a2093052_fk_accounts_emailuser_id;

ALTER TABLE wl_applications_applicationdeclineddetails
DROP CONSTRAINT wl_applications_appl_officer_id_79574921_fk_accounts_;

ALTER TABLE wl_applications_applicationrequest
DROP CONSTRAINT wl_applications_appl_officer_id_771456d0_fk_accounts_;

ALTER TABLE wl_applications_assessment
DROP CONSTRAINT wl_applications_asse_assigned_assessor_id_e6a39909_fk_accounts_;

ALTER TABLE wl_returns_return
DROP CONSTRAINT wl_returns_return_proxy_customer_id_b8485a01_fk_accounts_;

ALTER TABLE wl_returns_returnamendmentrequest
DROP CONSTRAINT wl_returns_returname_officer_id_0d7702ea_fk_accounts_;

ALTER TABLE wl_main_address
DROP CONSTRAINT wl_main_address_user_id_11db84da_fk_accounts_emailuser_id;

ALTER TABLE wl_applications_application
DROP CONSTRAINT wl_applications_appl_proxy_applicant_id_6338d187_fk_accounts_;

ALTER TABLE wl_applications_application
DROP CONSTRAINT wl_applications_appl_assigned_officer_id_1ba6f1d5_fk_accounts_;

ALTER TABLE wl_main_communicationslogentry
DROP CONSTRAINT wl_main_communicatio_staff_id_410a161a_fk_accounts_;

ALTER TABLE wl_main_licence
DROP CONSTRAINT wl_main_licence_holder_id_967f5856_fk_accounts_emailuser_id;

ALTER TABLE wl_main_licence
DROP CONSTRAINT wl_main_licence_issuer_id_3531ad92_fk_accounts_emailuser_id;

ALTER TABLE wl_applications_applicationuseraction
DROP CONSTRAINT wl_applications_appl_who_id_9f71daf0_fk_accounts_;

```

Drop the foreign key constraint from the reversion_revision table as well:

ALTER TABLE reversion_revision
DROP CONSTRAINT reversion_revision_user_id_17095f45_fk_accounts_emailuser_id;

**Step 11: Drop unused old m2m tables**
DROP TABLE wl_applications_application_documents_old CASCADE;
DROP TABLE wl_main_communicationslogentry_documents_old CASCADE;

**Step 12: Import the data from the products fixture::**

./manage.py loaddata wildlifelicensing/apps/main/fixtures/products.json

**Step 13: Create system groups from old auth group tables**

./manage.py create_system_group_permissions
