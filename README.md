Sales Performance & Customer Insights

DataCamp Capstone Project

Project Overview

This project analyzes sales performance and customer purchasing behavior using Python. It combines four datasets—customers, orders, order items, and products—to create an integrated dataset for sales analysis.

The goal is to understand business performance, identify revenue trends, evaluate product performance, and gain insights into customer purchasing behavior through data analysis and visualization.

Project Objectives

Analyze overall sales revenue and order performance.

Calculate key performance indicators (KPIs), including total revenue, total orders, and Average Order Value (AOV).

Identify the top 10 products based on revenue.

Examine revenue performance across product categories.

Analyze sales distribution across regions and cities.

Understand customer spending patterns.

Compare new and repeat customers.

Examine order statuses, including returns and cancellations.

Develop data-driven business insights and recommendations.

Tools and Technologies

Python – Data analysis and processing

Jupyter Notebook – Data cleaning and exploratory data analysis

Pandas – Data manipulation and integration

NumPy – Numerical operations

Matplotlib – Data visualization

Streamlit – Interactive dashboard development

GitHub – Project documentation and version control

Datasets

The project uses four datasets:

Dataset

Description

Customers

Customer information, demographics, and locations

Orders

Order dates, statuses, sales channels, discounts, and shipping information

Order Items

Products purchased, quantities, and purchase prices

Products

Product names, brands, categories, and pricing information

Data Cleaning and Preparation

The following data preparation activities were performed:

Inspected datasets for missing values, duplicates, and data types.

Removed exact duplicate records.

Standardized text values, including customer gender, names, locations, and product categories.

Handled missing customer information.

Converted date columns into datetime format.

Converted currency-formatted values into numeric data types.

Standardized product units of measurement.

Validated primary keys and foreign key relationships.

Identified and handled orphan records.

Integrated the four datasets into a consolidated fact table.

Key Performance Indicators

The following KPIs were calculated:

Total Revenue

Total Orders

Average Order Value (AOV)

Revenue was calculated using item quantity and purchase price, adjusted for the order discount.

The final sales analysis uses orders with Completed and Shipped statuses.

Data Analysis and Visualizations

The project includes the following analyses:

Monthly Revenue Trend – Examines revenue performance over time.

Top 10 Products by Revenue – Identifies the products generating the highest revenue.

Revenue by Product Category – Compares revenue contributions across categories.

Revenue by Region – Evaluates sales performance across geographical regions.

Customer Spending Distribution – Examines customer spending patterns.

New vs. Repeat Customers – Compares customers based on their number of orders in the analysis dataset.

Orders by Status – Examines the distribution of completed, shipped, pending, returned, and cancelled orders.

Interactive Dashboard

An interactive dashboard was developed using Streamlit to present the sales KPIs, product performance, customer insights, regional performance, and order status analysis.

The dashboard provides filters to explore sales performance across different dimensions.

Repository Contents

File/Folder

Description

README.md

Project overview and documentation

Executive Summary.txt

Executive summary of the capstone

CapstoneProject.ipynb

Jupyter Notebook containing data cleaning and analysis

data/

Cleaned datasets

charts/

Exported visualization images

app.py

Streamlit dashboard application

requirements.txt

Required Python libraries

One-Page Insights Summary.pdf

Summary of key findings and recommendations

How to Run the Dashboard

Install the required libraries:

pip install -r requirements.txt

Run the Streamlit application:

streamlit run app.py

Project Deliverables

Completed Jupyter Notebook

Cleaned datasets

Sales performance visualizations

Interactive Streamlit dashboard

Executive Summary

One-Page Insights Summary

Business insights and recommendations

Conclusion

This capstone demonstrates the use of Python for data cleaning, data integration, exploratory analysis, KPI calculation, and visualization. The resulting dashboard provides an interactive way to explore sales and customer performance and supports data-driven business decision-making.