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