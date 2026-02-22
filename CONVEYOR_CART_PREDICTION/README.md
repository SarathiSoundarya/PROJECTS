# Conveyor Cart Availability Forecasting System

## Project Overview

This project builds a machine learning system to monitor and forecast the availability of automated conveyor carts operating inside a factory.

The factory has around 25 conveyor carts that continuously transport materials between stations. These carts are always running and can be in one of three states:

0 → Carrying Load

1 → Empty / Ready

2 → Under Maintenance

The data records the state of all carts as and when the state of the cart changes.

The project:

Counts how many are loaded, empty, or under maintenance

Uses these aggregated features to forecast how many carts will be available/ready in the next operational cycles

The model uses XGBoost Regression for multi-horizon forecasting.


## What is XGBoost
Instead of building one large model, XGBoost builds:


𝐾
K = number of trees

Each tree corrects the errors of the previous one
## Why We Chose XGBoost

We chose XGBoost because:

- It captures non-linear relationships

- It has built-in regularization (reduces overfitting)

In real-world production systems, XGBoost is often preferred for reliability and performance.