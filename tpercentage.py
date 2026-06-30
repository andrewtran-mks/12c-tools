import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import itertools

st.title("12C T% Curve Comparison Tool (Internal Reports only)")
st.write("Upload up to 10 Internal Reports (.xlsm), select HO/ZO and Donut/Tophat, and compare Transmission curves.")

# Upload up to 10 Internal Reports
uploaded_files = st.file_uploader(
    "Upload Excel files (max 10)", 
    type=["xlsx", "xlsm"], 
    accept_multiple_files=True
)

if uploaded_files and len(uploaded_files) > 10:
    st.error("Please upload no more than 10 files.")
    st.stop()

# HO/ZO selector
category_hozo = st.selectbox("Select HO or ZO:", ["HO", "ZO"])

# Donut/Tophat selector
category_shape = st.selectbox("Select Donut or Tophat:", ["Donut", "TopHat"])

# Preset X‑axis ranges
preset_ranges = {
    1:  (500.5, 515.5),
    2:  (523.5, 540.5),
    3:  (548.5, 565.5),
    4:  (572.5, 591.5),
    5:  (598.5, 617.5),
    6:  (627.5, 644.5),
    7:  (660.5, 679.5),
    8:  (695.5, 714.5),
    9:  (731.5, 752.5),
    10: (768.0, 787.0),
    11: (825.0, 852.0),
    12: (873.5, 896.5)
}

st.write("### Choose T% Range")
preset_choice = st.selectbox("Channels 1–12:", list(preset_ranges.keys()))
preset_min, preset_max = preset_ranges[preset_choice]

st.write("### Enter Wavelength Range")
x_min = st.number_input(
    "Minimum Wavelength (nm)",
    min_value=497.0,
    max_value=903.0,
    value=preset_min,
    step=0.5
)

x_max = st.number_input(
    "Maximum Wavelength (nm)",
    min_value=497.0,
    max_value=903.0,
    value=preset_max,
    step=0.5
)


if x_min > x_max:
    st.error("Minimum X value cannot be greater than maximum X value.")
    st.stop()

if uploaded_files:
    st.write("### Select which files to include")
    file_toggles = {}
    for file in uploaded_files:
        file_toggles[file.name] = st.checkbox(f"{file.name}", value=True)

    col_plot, col_table = st.columns([2, 1])

    fig, ax = plt.subplots(figsize=(10, 6))
    color_cycle = itertools.cycle(plt.rcParams['axes.prop_cycle'].by_key()['color'])

    # table to store uniformity
    diff_rows = []

    for file in uploaded_files:
        if not file_toggles[file.name]:
            continue  # skip files toggled OFF

        df = pd.read_excel(file, sheet_name=6, engine="openpyxl")

        # filter by HO/ZO, donut/tophat, and sample = 0 (omitting -1 and 1)
        df_f = df[
    (df.iloc[:, 3] == category_hozo) &
    (df.iloc[:, 7] == category_shape) &
    (df.iloc[:, 9] == 0)
]


        # extract columns L and P
        x = df_f.iloc[:, 11]
        y = df_f.iloc[:, 15]

        # apply x‑axis filtering
        mask = (x >= x_min) & (x <= x_max)
        x_f, y_f = x[mask], y[mask]

        # sort by x-value
        df_sorted = pd.DataFrame({"x": x_f, "y": y_f}).sort_values("x")

        if len(df_sorted) < 2:
            continue

        #compute reduced band uniformity
        y_diff = abs(df_sorted["y"].max() - df_sorted["y"].min()) * 100

        # store for table
        diff_rows.append({
            "File": file.name,
            "Uniformity": y_diff
        })

        # plot
        color = next(color_cycle)
        ax.scatter(df_sorted["x"], df_sorted["y"], s=40, color=color)
        ax.plot(df_sorted["x"], df_sorted["y"], label=f"{file.name}", color=color)

    # Toggle for fixed Y-axis range
    use_fixed_y = st.checkbox("Use fixed Y-axis range (0.68 to 0.95)", value=False)

    # Finalize plot
    ax.set_xlabel("Wavelength")
    ax.set_ylabel("Transmission")
    ax.set_title(f"Comparison of Wavelength vs. Transmission ({category_hozo}, {category_shape})")
    ax.grid(True)
    
    if use_fixed_y:
        ax.set_ylim(0.68, 0.95)


    # Legend below plot
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=2,
        frameon=True
    )

    with col_plot:
        st.pyplot(fig)

    with col_table:
        st.write("### Y‑Difference (Within Range)")
        if diff_rows:
            st.dataframe(pd.DataFrame(diff_rows))
        else:
            st.write("No valid data in selected range or all files toggled off.")
