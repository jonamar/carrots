# Carrots

A tool designed to calculate the total kilograms of carrots ordered from Lufa Farms over time. 

## Overview

This repository contains scripts to track and analyze carrot orders from Lufa Farms. It helps users monitor their carrot consumption patterns over specified time periods and provides valuable insights through key performance indicators (KPIs).

## Usage

1. Place your invoices in the `pdfs` directory. 
2. Run the main script to calculate your total carrot orders:

```bash
python harvest_carrots_kg.py
```

You can customize the average carrot weight (default is 100g) using the `--avg-carrot-weight` parameter:

```bash
python harvest_carrots_kg.py --avg-carrot-weight 120
```

## Purpose

This tool was created to help Lufa Farms customers track their carrot consumption habits and analyze ordering patterns over time.

## Key Performance Indicators (KPIs)

The tool calculates and displays the following KPIs:

- **Total carrot weight**: The total weight of carrots ordered in kilograms
- **Estimated total carrots**: Approximate number of individual carrots based on average carrot weight
- **CPO (Carrots Per Order)**: Average number of carrots per order
- **Oldest order date**: Date of the earliest order in the dataset
- **Carrot Top Month**: The month with the highest carrot order volume, showing both weight and estimated number of carrots
- **Average orders per month**: The average number of orders placed per month

## Credits

This codebase was written by AI Claude 3.7 Sonnet and architected by Jon Amar.
