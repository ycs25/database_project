import pandas as pd
from pathlib import Path
import os

# Determine CSV locations
BASE_DIR = Path(__file__).parent.resolve()
CSV_DIR = Path(os.environ.get('CASE_CSV_DIR', BASE_DIR))

df_year = pd.read_csv(CSV_DIR / 'cases_year.csv')
df_month = pd.read_csv(CSV_DIR / 'cases_month.csv')

print("DataFrames loaded successfully.")

region_mapping = {
    'AFRO': 'AFR', 'EURO': 'EUR', 'WPRO': 'WPR', 'AMRO': 'AMR',
    'EMRO': 'EMR', 'SEARO': 'SEAR', 'AFR': 'AFR', 'EUR': 'EUR',
    'WPR': 'WPR', 'AMR': 'AMR', 'EMR': 'EMR', 'SEAR': 'SEAR'
}

# Standardize region column in df_year
df_year['region'] = df_year['region'].map(region_mapping)

# Standardize region column in df_month
df_month['region'] = df_month['region'].map(region_mapping)

# Create countries_df from unique combinations of 'iso3', 'country', and 'region'
countries_df_year = df_year[['iso3', 'country', 'region']].drop_duplicates()
countries_df_month = df_month[['iso3', 'country', 'region']].drop_duplicates()

countries_df = pd.concat([countries_df_year, countries_df_month], ignore_index=True)
countries_df = countries_df.drop_duplicates(subset=['iso3'])
countries_df.dropna(subset=['country'], inplace=True)

# Create date column in df_month
df_month['date'] = pd.to_datetime(df_month['year'].astype(str) + '-' + df_month['month'].astype(str) + '-01')

# Select relevant columns for case_data_df and fill NaNs
case_columns = [
    'measles_suspect', 'measles_clinical', 'measles_epi_linked',
    'measles_lab_confirmed', 'measles_total', 'rubella_clinical',
    'rubella_epi_linked', 'rubella_lab_confirmed', 'rubella_total', 'discarded'
]

case_data_df = df_month[['iso3', 'date'] + case_columns].copy()
case_data_df[case_columns] = case_data_df[case_columns].fillna(0)

print("Data preprocessing complete. Standardized regions, created countries_df, added date column, and prepared case_data_df.")

print("\n--- countries_df Head ---")
print(countries_df.head())

print("\n--- df_month with date column Head ---")
print(df_month[['year', 'month', 'date']].head())

print("\n--- case_data_df Head ---")
print(case_data_df.head())

print("\n--- case_data_df Info (check for NaNs in case columns) ---")
case_data_df.info()

from peewee import SqliteDatabase, Model, CharField, DateField, IntegerField, FloatField, ForeignKeyField

# Create an instance of SqliteDatabase
database = SqliteDatabase('measles_rubella.db')

# Define a BaseModel class
class BaseModel(Model):
    class Meta:
        database = database

# Define the Country model
class Country(BaseModel):
    iso3 = CharField(primary_key=True)
    country = CharField()
    region = CharField()

    class Meta:
        table_name = 'country'

# Define the CaseData model
class CaseData(BaseModel):
    country_iso3 = ForeignKeyField(Country, to_field='iso3', backref='cases')
    date = DateField()
    measles_suspect = FloatField(null=True)
    measles_clinical = FloatField(null=True)
    measles_epi_linked = FloatField(null=True)
    measles_lab_confirmed = FloatField(null=True)
    measles_total = FloatField(null=True)
    rubella_clinical = FloatField(null=True)
    rubella_epi_linked = FloatField(null=True)
    rubella_lab_confirmed = FloatField(null=True)
    rubella_total = FloatField(null=True)
    discarded = FloatField(null=True)

    class Meta:
        table_name = 'case_data'
        indexes = (
            (('country_iso3', 'date'), True), # Ensure unique combination of country and date
        )

print("Peewee ORM models (Country and CaseData) defined successfully.")

database.connect()
database.create_tables([Country, CaseData])

print("Database connected and tables created successfully.")

import peewee

country_data_to_insert = countries_df.to_dict(orient='records')

with database.atomic():
    for batch in peewee.chunked(country_data_to_insert, 100):
        try:
            # Ignore conflicts on primary key (iso3) so reruns don't crash
            Country.insert_many(batch).on_conflict(action='IGNORE').execute()
        except AttributeError:
            # Fallback if peewee version doesn't support on_conflict on insert_many
            for rec in batch:
                try:
                    Country.insert(**rec).on_conflict(action='IGNORE', conflict_target=[Country.iso3]).execute()
                except Exception:
                    # Final fallback: try insert and ignore IntegrityError
                    try:
                        Country.insert(**rec).execute()
                    except Exception:
                        pass

print(f"Inserted/ignored {len(countries_df)} country records into the Country table.")

case_data_to_insert = case_data_df.rename(columns={'iso3': 'country_iso3'}).to_dict(orient='records')

with database.atomic():
    for batch in peewee.chunked(case_data_to_insert, 1000):
        try:
            # Ignore conflicts on the (country_iso3, date) unique index
            CaseData.insert_many(batch).on_conflict(action='IGNORE').execute()
        except AttributeError:
            # Fallback: insert row-by-row with conflict-ignore logic
            for rec in batch:
                try:
                    CaseData.insert(**rec).on_conflict(action='IGNORE', conflict_target=[CaseData.country_iso3, CaseData.date]).execute()
                except Exception:
                    try:
                        CaseData.insert(**rec).execute()
                    except Exception:
                        pass

print(f"Inserted/ignored {len(case_data_df)} case data records into the CaseData table.")

import datetime

def get_cases_by_country(iso3_code):
    # Returns all case data records for a specific country by ISO3 code
    try:
        country = Country.get_or_none(Country.iso3 == iso3_code.upper())
        if country:
            print(f"Retrieving case data for {country.country} ({country.iso3})...")
            cases = CaseData.select().where(CaseData.country_iso3 == iso3_code.upper()).order_by(CaseData.date)
            if cases.count() > 0:
                return list(cases)
            else:
                print(f"No case data found for {country.country} ({country.iso3}).")
                return []
        else:
            print(f"Country with ISO3 code '{iso3_code}' not found.")
            return []
    except Exception as e:
        print(f"Error retrieving cases for {iso3_code}: {e}")
        return []

def get_cases_by_date_range(start_date_str, end_date_str, iso3_code=None):
    # Returns case data records within a date range, optionally filtered by country
    try:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()

        query = CaseData.select().where(CaseData.date.between(start_date, end_date)).order_by(CaseData.date)

        if iso3_code:
            country = Country.get_or_none(Country.iso3 == iso3_code.upper())
            if country:
                print(f"Retrieving case data for {country.country} ({country.iso3}) between {start_date_str} and {end_date_str}...")
                query = query.where(CaseData.country_iso3 == iso3_code.upper())
            else:
                print(f"Country with ISO3 code '{iso3_code}' not found. Querying all countries for the date range.")
        else:
            print(f"Retrieving case data for all countries between {start_date_str} and {end_date_str}...")

        cases = list(query)
        if cases:
            return cases
        else:
            print(f"No case data found for the specified criteria.")
            return []
    except ValueError:
        print("Invalid date format. Please use 'YYYY-MM-DD'.")
        return []
    except Exception as e:
        print(f"Error retrieving cases by date range: {e}")
        return []

def get_country_info(iso3_code):
    # Returns country name and region for a given ISO3 code
    try:
        country = Country.get_or_none(Country.iso3 == iso3_code.upper())
        if country:
            print(f"Retrieving info for country with ISO3 code '{iso3_code}'...")
            return {'iso3': country.iso3, 'country': country.country, 'region': country.region}
        else:
            print(f"Country with ISO3 code '{iso3_code}' not found.")
            return None
    except Exception as e:
        print(f"Error retrieving country info for {iso3_code}: {e}")
        return None

print("\n--- Demonstrating Query Functions ---\n")

# Get country info
print("Get country information for DZA")
dza_info = get_country_info('DZA')
if dza_info:
    print(f"ISO3: {dza_info['iso3']}, Country: {dza_info['country']}, Region: {dza_info['region']}")
else:
    print("Country information not found.")

print("\nGet country information for a non-existent code")
non_existent_info = get_country_info('XYZ')
if non_existent_info:
    print(non_existent_info)
else:
    print("Country information not found as expected.")

# Get cases by country
print("\nGet cases for Algeria (DZA)")
algeria_cases = get_cases_by_country('DZA')
if algeria_cases:
    print(f"Found {len(algeria_cases)} records for Algeria. First 3 records:")
    for case in algeria_cases[:3]:
        print(f"  Date: {case.date}, Measles Total: {case.measles_total}, Rubella Total: {case.rubella_total}")
else:
    print("No cases found for Algeria.")

print("\nGet cases for a non-existent country")
non_existent_cases = get_cases_by_country('ABC')
if not non_existent_cases:
    print("No cases found for non-existent country as expected.")

# Get cases by date range for a specific country
print("\nGet cases for Algeria (DZA) in 2012")
algeria_2012_cases = get_cases_by_date_range('2012-01-01', '2012-12-31', 'DZA')
if algeria_2012_cases:
    print(f"Found {len(algeria_2012_cases)} records for Algeria in 2012. First 3 records:")
    for case in algeria_2012_cases[:3]:
        print(f"  Date: {case.date}, Measles Total: {case.measles_total}")
else:
    print("No cases found for Algeria in 2012.")

# Get cases by date range for all countries
print("\nGet cases for all countries in January 2012 (first 5 records)")
jan_2012_cases = get_cases_by_date_range('2012-01-01', '2012-01-31')
if jan_2012_cases:
    print(f"Found {len(jan_2012_cases)} records for January 2012. First 5 records:")
    for case in jan_2012_cases[:5]:
        country_name = Country.get_or_none(Country.iso3 == case.country_iso3)
        print(f"  Country: {country_name.country if country_name else case.country_iso3}, Date: {case.date}, Measles Total: {case.measles_total}")
else:
    print("No cases found for January 2012.")

# Get cases by date range with no results
print("\nGet cases for a future date range (expect no results)")
future_cases = get_cases_by_date_range('2030-01-01', '2030-12-31', 'DZA')
if not future_cases:
    print("No cases found for future date range as expected.")

# In case of invalid date format
print("\nTest invalid date format")
invalid_date_cases = get_cases_by_date_range('2012/01/01', '2012-01-31', 'DZA')
if not invalid_date_cases:
    print("Invalid date format handled as expected.")

if database.is_closed():
    database.connect()

print("--- Verifying Database Data ---")

# Verify total count of records in Country table
country_count = Country.select().count()
print(f"Total records in Country table: {country_count}")

# Expected count is based on the countries_df
expected_country_count = len(countries_df)
if country_count == expected_country_count:
    print(f"Country table count matches expected count ({expected_country_count}).")
else:
    print(f"WARNING: Country table count ({country_count}) does not match expected count ({expected_country_count}).")

# Verify total count of records in CaseData table
case_data_count = CaseData.select().count()
print(f"Total records in CaseData table: {case_data_count}")

# Expected count is based on the case_data_df
expected_case_data_count = len(case_data_df)
if case_data_count == expected_case_data_count:
    print(f"CaseData table count matches expected count ({expected_case_data_count}).")
else:
    print(f"WARNING: CaseData table count ({case_data_count}) does not match expected count ({expected_case_data_count}).")

# Retrieve information for a specific country
print("\n--- Retrieving info for DZA (Algeria) ---")
dza_info = get_country_info('DZA')
if dza_info:
    print(f"ISO3: {dza_info['iso3']}, Country: {dza_info['country']}, Region: {dza_info['region']}")
else:
    print("Could not retrieve info for DZA.")

# Retrieve a few case data records for 'DZA'
print("\n--- Retrieving first 5 case data records for DZA ---")
algeria_cases_sample = get_cases_by_country('DZA')
if algeria_cases_sample:
    print(f"Found {len(algeria_cases_sample)} records for Algeria. First 5 records:")
    for case in algeria_cases_sample[:5]:
        print(f"  Date: {case.date}, Measles Total: {case.measles_total}, Rubella Total: {case.rubella_total}, Discarded: {case.discarded}")
else:
    print("No case data found for DZA.")

# Close the database connection if desired, or leave open for further operations
# database.close()
# print("Database connection closed.")