import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from xgboost import XGBRegressor
import traceback
import plotly.graph_objects as go
import logging

#RUN COMMAND: 

class Model:

    def __init__(self, timestamp_unit="s"):

        self.input_params = [
            'CONVEYOR_STATUS_16', 'CONVEYOR_STATUS_03', 'CONVEYOR_STATUS_04',
            'CONVEYOR_STATUS_01', 'CONVEYOR_STATUS_06', 'CONVEYOR_STATUS_08',
            'CONVEYOR_STATUS_05', 'CONVEYOR_STATUS_12', 'CONVEYOR_STATUS_09',
            'CONVEYOR_STATUS_07', 'CONVEYOR_STATUS_02', 'CONVEYOR_STATUS_13',
            'CONVEYOR_STATUS_17', 'CONVEYOR_STATUS_22', 'CONVEYOR_STATUS_14',
            'CONVEYOR_STATUS_11', 'CONVEYOR_STATUS_20', 'CONVEYOR_STATUS_19',
            'CONVEYOR_STATUS_21', 'CONVEYOR_STATUS_25', 'CONVEYOR_STATUS_23',
            'CONVEYOR_STATUS_24', 'CONVEYOR_STATUS_27', 'CONVEYOR_STATUS_26',
            'CONVEYOR_STATUS_29'
        ]

        self.timestamp_unit = "s"
        self.timestamp_factor = 1 if self.timestamp_unit == 's' else 1000
        self.logger = logging.getLogger("ML MODEL LOGGER")
        self.logger.setLevel(logging.INFO)
        if not self.logger.hasHandlers():
            stream_handler = logging.StreamHandler()
            self.logger.addHandler(stream_handler)


    def predict(self, data):
        try:
            self.logger.info("Prediction started")
            missing_cols = list(set(self.input_params) - set(data.columns))
            if missing_cols:
                self.logger.info("Missing Columns")
                return {
                    "status":"error",
                    "message": f"Missing columns: {missing_cols}"
                }
            

            data["TIMESTAMP"] = pd.to_datetime(
                data["TIMESTAMP"],
                unit=self.timestamp_unit,
                errors="coerce"
            )

            data = data.sort_values("TIMESTAMP")


            # resample----------------------->
            df_resampled = (
                data
                .ffill()
                .set_index("TIMESTAMP")
                .resample("1min")
                .first()
                .ffill()
                .fillna(0).reset_index()
            )

            if df_resampled.empty:
                self.logger.info("Resampled data is empty!")
                return pd.DataFrame({
                    "status":"error",
                    "message": "No data after resampling"})
        
            duration_minutes = (df_resampled["TIMESTAMP"].max() - df_resampled["TIMESTAMP"].min()).total_seconds() / 60

            if duration_minutes < 15:
                self.logger.info("Insufficient duration of data, past 15 mins data unavailable")
                return {
                    "status":"error",
                    "message": f"Insufficient data duration: {duration_minutes:.2f} minutes. At least 15 minutes of historical data is required for prediction."
                }
            
            self.logger.info("Resampled sucessfully!")

            # feature engineering----------------------->
            conveyor_cols = [
                col for col in df_resampled.columns
                if col.startswith("CONVEYOR_STATUS")
            ]

            df_resampled["num_carts_full"] = (df_resampled[conveyor_cols] == 0).sum(axis=1)
            df_resampled["num_carts_empty"] = (df_resampled[conveyor_cols] == 1).sum(axis=1)
            df_resampled["num_carts_maintenance"] = (df_resampled[conveyor_cols] == 2).sum(axis=1)

            
            feature_df_15 = self.create_cart_features(df_resampled, 3)
            feature_df_30 = self.create_cart_features(df_resampled, 5)
            feature_df_45 = self.create_cart_features(df_resampled, 10)
            feature_df_60 = self.create_cart_features(df_resampled, 15)
            self.logger.info("Feature engineering done!")
            if feature_df_15.empty or feature_df_30.empty or feature_df_45.empty or feature_df_60.empty:
                self.logger.info("Feature data frame is empty!")
                return {
                    "status":"error",
                    "message": "Insufficient data after feature engineering. Please provide more historical data for accurate predictions."
                }
            
            feature_map = {
                15: feature_df_15,
                30: feature_df_30,
                45: feature_df_45,
                60: feature_df_60
            }
            feature_cols = [
            'num_carts_full',
            'num_carts_empty',
            'num_carts_maintenance',

            'num_carts_full_lag1',
            'num_carts_empty_lag1',
            'num_carts_maintenance_lag1',

            'num_carts_full_roll_mean',
            'num_carts_empty_roll_mean',
            'num_carts_maintenance_roll_mean',

            'num_carts_full_roll_std',
            'num_carts_empty_roll_std',
            'num_carts_maintenance_roll_std',

            'num_carts_full_diff1',
            'num_carts_empty_diff1',
            'num_carts_maintenance_diff1'
            ]


            BASE_DIR = Path(__file__).resolve().parent
            predictions = {}
            plots = {}
            for mins, fdf in feature_map.items():

                fname = f"xgb_regressor_cart{mins}min.json"
                model_path = BASE_DIR / "model_files" / fname

                model = XGBRegressor()
                model.load_model(model_path)

                preds = model.predict(fdf[feature_cols])
                last_pred = int(np.rint(preds[-1]))
                predictions[f"PRED_{mins}"] = last_pred

                # store plot
                plots[mins] = (fdf["TIMESTAMP"], preds)
                self.logger.info(f"Predicted {mins} min")

            result = {
                "status": "success",
                "predictions": predictions,
                "plots": plots,
                "resampled": df_resampled
            }
            self.logger.info("Returning result")

            return result
        except Exception as e:
            self.logger.error("An error occurred during prediction.  Error details: " + str(e) + "\n" + traceback.format_exc())
            return {
                "status":"error",
                "message": "An error occurred during prediction.  Error details: " + str(e) + "\n" + traceback.format_exc()
            }

    def create_cart_features(self,df, roll_window):

        df = df.sort_values("TIMESTAMP").reset_index(drop=True).copy()

        base_cols = ["num_carts_full", "num_carts_empty", "num_carts_maintenance"]

        # -------------------------
        # Lag Features
        # -------------------------
        for col in base_cols:
            df[f"{col}_lag1"] = df[col].shift(1)

        # -------------------------
        # Rolling Mean + Std
        # -------------------------
        for col in base_cols:
            df[f"{col}_roll_mean"] = df[col].rolling(roll_window).mean()
            df[f"{col}_roll_std"] = df[col].rolling(roll_window).std()

        # -------------------------
        # Difference / Momentum
        # -------------------------
        for col in base_cols:
            df[f"{col}_diff1"] = df[col].diff(1)

        # Drop rows where target not available
        df = df.dropna().reset_index(drop=True)

        return df
    
# ==============================
# STREAMLIT UI
# ==============================

st.title("🚀 Conveyor Prediction App")

st.write(
    "Upload a CSV containing TIMESTAMP and conveyor status columns."
)

#upload a file
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if st.button("Run Prediction"):

    if uploaded_file is not None:
        try:
            # FILE TYPE VALIDATION
            if not uploaded_file.name.lower().endswith(".csv"):
                st.error("Uploaded file is not a CSV.")
                st.stop()

            df = pd.read_csv(uploaded_file)

            st.subheader("Input Data Preview")
            st.dataframe(df.head())

            model = Model()

            output = model.predict(df)

            if output["status"] == "error":

                st.error(output["message"])

            else:

                st.success("Prediction Completed")

                st.subheader("Predictions")
                st.write(output["predictions"])

                st.subheader("Resampled Data")
                st.dataframe(output["resampled"].tail())

                st.subheader("Prediction Plots")
                            
                for mins, (ts, preds) in output["plots"].items():

                    fig = go.Figure()

                    fig.add_trace(
                        go.Scatter(
                            x=ts,
                            y=preds,
                            mode="lines",
                            name=f"{mins} Min Prediction"
                        )
                    )

                    fig.update_layout(
                        title=f"{mins} Minute Prediction",
                        xaxis_title="Timestamp",
                        yaxis_title="Predicted Available Carts",
                        template="plotly_white"
                    )

                    st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Error: {e}")

    else:
        st.warning("Please upload a CSV file to run predictions.")