import pandas as pd
import numpy as np
from peewee import SqliteDatabase, Model, CharField, DateField, IntegerField, FloatField, ForeignKeyField

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

def get_monthly_cases():
    query = CaseData.select(Country, CaseData).join(Country)
    monthly_cases = pd.DataFrame(list(query.dicts()))
    monthly_cases.drop(columns=['id', 'country_iso3'], inplace=True, errors='ignore')
    return monthly_cases

def get_countries():
    fields_to_select = [f for f in Country._meta.sorted_fields if f.name != 'id']
    query = Country.select(*fields_to_select)
    countries = pd.DataFrame(list(query.dicts()))
    return countries

if  __name__ == '__main__':
    print(get_countries().head())
    print(get_monthly_cases().head())

