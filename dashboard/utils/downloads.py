"""CSV download helpers for dashboard pages."""

import streamlit as st


def csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")


def download_dataframe(df, file_name, label="Descargar CSV", key=None):
    st.download_button(
        label=label,
        data=csv_bytes(df),
        file_name=file_name,
        mime="text/csv",
        key=key,
        use_container_width=True,
    )
