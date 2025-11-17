# 📈 Measles & Rubella Global Case Data Analysis Dashboard

This project aims to develop a fully functional, interactive web application for analyzing global measles and rubella case data provided by the World Health Organization (WHO). The application will showcase a complete modern data workflow, integrating database management, data cleaning, and web visualization.

## ✨ Core Features & Project Rationale

The dashboard provides a valuable tool for monitoring and comparing the measles burden globally and regionally, directly addressing critical public health data analysis needs. It is capable of highlighting regions with consistently high measles burdens.

## 📊 Dashboard Usability

The project is considered successful when users can successfully:
- Filter the data by **WHO Region** and specific **Country**.
- View **time-series charts** of total measles cases over time.
- View a **ranking or comparison chart** of countries based on the **Laboratory Confirmed Case Ratio** to gauge healthcare capacity differences.

## 🛠️ Tech Stack & Architecture

The project demonstrates the successful integration of a Full Stack composed of four distinct technologies:

|Layer|Technology|Purpose|
|---|---|---|---|
|Database (DB)|SQLite|To efficiently store the spatio-temporal data.|
|Data Layer / ORM|Peewee|"Used to define models, establish the database connection, and perform all data access."|
|Data Processing|Pandas / Python|"Data engineering, cleaning, and implementing the ETL process."|
|Presentation Layer|Streamlit|"To build the dynamic, interactive web application and visualizations."|

💡 Technical Interest & Novelty
- **Full Stack Demonstration:** Successfully integrates SQLite, Peewee, Pandas, and Streamlit.
- **Spatiotemporal Querying:** The application requires efficient querying of data based on both **geographic location** (country, region) and **time** (year, month), demonstrating advanced data retrieval logic.

## 🛣️ Project Phases

1. Data Engineering & Cleaning (Python/Pandas):
    - Load the datasets.
    - Convert all character-type numerical variables (e.g., case counts, population, incidence rates) into the appropriate numeric data types for storage and calculation.
2. Database Design & Implementation (SQLite/Peewee):
    - Design a relational schema.
    - Implement the schema using the **Peewee ORM** to define models and establish the connection to a SQLite database instance.
    - Develop a Python script to perform the **ETL** (Extract, Transform, Load) process, populating the SQLite tables with the cleaned data.
3. Interactive Dashboard Development (Streamlit):
    - Build a dynamic Streamlit application that connects to the SQLite database via the Peewee ORM.
    - Implement interactive controls (e.g., dropdowns for region/country, time-range sliders) to allow users to filter and query the database.
    - Visualize key metrics.

## ✅ Success Criteria

The project will be considered successful when the following criteria are met:
1. **Database Integrity:** The SQLite database is fully populated with the cleaned WHO data, with all critical variables (case counts, population, incidence rates) stored as the appropriate data type.
2. **ORM Functionality:** All data access within the Streamlit application is performed exclusively through the Peewee ORM models.
3. **Dashboard Usability:** The Streamlit application is running and responsive, and all features listed in the Core Features section are implemented.
4. **Documentation:** A final presentation/documentation is submitted, including the **schema diagram**, the **Peewee ORM model definitions**, and a link to the **complete source code**.