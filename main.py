import streamlit as st
import plotly.express as px
import plotly.figure_factory as ff
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

# ====================================
# PAGE CONFIG
# ====================================
st.set_page_config(
    page_title="Stress bei Studierenden",
    layout="wide"
)

st.title("Stressanalyse bei Studierenden")
st.markdown(
    """
    <style>
        .block-container { padding-top: 4rem; }
    </style>
    """,
    unsafe_allow_html=True
)

st.divider()

from pathlib import Path
DATA_PATH = Path(_file_).parent / "stress_studierende_dashboard.csv"
df = pd.read_csv(DATA_PATH)

# (optional) Debug – kannst du später löschen
# st.write("Daten geladen:", df.shape)

def chart_with_data(fig, data_df, label="Daten anzeigen"):
    st.plotly_chart(fig, use_container_width=True)
    with st.expander(label):
        st.dataframe(data_df)

# ====================================
# SIDEBAR FILTER (Single-Select)
# ====================================
st.sidebar.header("Choose your filter")

studiengang = st.sidebar.selectbox(
    "Studiengang",
    options=["Alle"] + sorted(df["Studiengang"].dropna().unique().tolist()),
    index=0
)

semester = st.sidebar.selectbox(
    "Semester",
    options=["Alle"] + sorted(df["Semester"].dropna().unique().tolist()),
    index=0
)

filtered_df = df.copy()

if studiengang != "Alle":
    filtered_df = filtered_df[filtered_df["Studiengang"] == studiengang]

if semester != "Alle":
    filtered_df = filtered_df[filtered_df["Semester"] == semester]

# ====================================
# 0. KONTEXT / EINORDNUNG + MINI-KPIs
# ====================================

stress_threshold = 5
n_total = len(filtered_df)

if n_total == 0:
    st.warning("Keine Daten nach Filterauswahl.")
else:
    stress_rate = (filtered_df["Stresslevel"] >= stress_threshold).mean() * 100
    avg_stress = pd.to_numeric(filtered_df["Stresslevel"], errors="coerce").mean()
    avg_sleep = pd.to_numeric(filtered_df["Schlafstunden"], errors="coerce").mean()

    st.markdown(
        f"""
Die folgenden Analysen basieren auf einer Stichprobe von *n = {n_total}* Studierenden aus verschiedenen Studiengängen und Semestern.
Stress wird anhand eines standardisierten Stresslevels erfasst. Ziel ist es, Zusammenhänge zwischen Stress, Leistung und Bewältigungsstrategien sichtbar zu machen.
        """
    )

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Anzahl Studierende (n)", f"{n_total}")
    k2.metric("Anteil gestresst", f"{stress_rate:.1f}%")
    k3.metric("Ø Stresslevel", f"{avg_stress:.2f}")
    k4.metric("Ø Schlafdauer", f"{avg_sleep:.2f} h")

    st.divider()


# ====================================
# DIAGRAMM 1–3 (oben)
# ====================================
c1, c2, c5 = st.columns(3)

with c1:
    st.subheader("Stress (ja / nein)")

    stress_threshold = 5
    stress_status = filtered_df["Stresslevel"].apply(
        lambda x: "Stress" if float(x) >= stress_threshold else "Kein Stress"
    )

    pie_df = stress_status.value_counts().reset_index()
    pie_df.columns = ["Status", "Anzahl"]

    fig1 = px.pie(
        pie_df,
        names="Status",
        values="Anzahl",
        color="Status",
        color_discrete_map={"Kein Stress": "#2ecc71", "Stress": "#e74c3c"}
    )
    fig1.update_traces(textposition="inside", textinfo="percent+label")
    fig1.update_layout(legend_title="Status")

    chart_with_data(fig1, pie_df, "Daten anzeigen")


with c2:
    st.subheader("Stresslevel-Gruppen")

    grp_df = filtered_df["Stressgruppe"].value_counts().reset_index()
    grp_df.columns = ["Stressgruppe", "Anzahl"]

    fig_grp = px.pie(grp_df, names="Stressgruppe", values="Anzahl", template="gridon")
    fig_grp.update_traces(textposition="inside")

    chart_with_data(fig_grp, grp_df, "Daten anzeigen")


with c5:
    st.subheader("Stress nach Studiengang")

    stud_df = filtered_df["Studiengang"].value_counts().reset_index()
    stud_df.columns = ["Studiengang", "Anzahl"]

    fig2 = px.pie(stud_df, names="Studiengang", values="Anzahl", hole=0.5)
    fig2.update_traces(textposition="outside")
    fig2.update_layout(legend_title="Studiengang")

    chart_with_data(fig2, stud_df, "Daten anzeigen")

st.divider()

# ====================================
# LEISTUNG — 2 CHARTS NEBENEINANDER
# ====================================
st.subheader("Leistung & Stress")
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("*Leistung in Abhängigkeit vom Stressniveau*")

    if "Leistung" not in filtered_df.columns:
        st.error("Spalte 'Leistung' fehlt in der CSV.")
    else:
        tmp = filtered_df.copy()
        tmp["Stresslevel"] = pd.to_numeric(tmp["Stresslevel"], errors="coerce")
        tmp["Leistung"] = pd.to_numeric(tmp["Leistung"], errors="coerce")
        tmp = tmp.dropna(subset=["Stresslevel", "Leistung"])

        perf_df = tmp.groupby("Stresslevel", as_index=False)["Leistung"].mean().sort_values("Stresslevel")

        all_stress = pd.DataFrame({"Stresslevel": list(range(1, 11))})
        perf_df = all_stress.merge(perf_df, on="Stresslevel", how="left")
        perf_df["Leistung"] = perf_df["Leistung"].interpolate()

        fig_perf = px.line(perf_df, x="Stresslevel", y="Leistung", markers=True, template="gridon")
        fig_perf.update_xaxes(
            tickmode="array", tickvals=list(range(1, 11)), ticktext=[str(i) for i in range(1, 11)],
            range=[1, 10], title="Stressniveau"
        )
        fig_perf.update_yaxes(
            range=[0.5, 10.5], tickmode="linear", tick0=1, dtick=1, title="Leistung"
        )

        chart_with_data(fig_perf, perf_df, "Daten anzeigen")

with col_right:
    st.markdown("*Ø Leistung: Stress vs Kein Stress*")

    if "Leistung" not in filtered_df.columns:
        st.error("Spalte 'Leistung' fehlt in der CSV.")
    else:
        stress_threshold = 5

        tmp = filtered_df.copy()
        tmp["Stresslevel"] = pd.to_numeric(tmp["Stresslevel"], errors="coerce")
        tmp["Leistung"] = pd.to_numeric(tmp["Leistung"], errors="coerce")
        tmp = tmp.dropna(subset=["Stresslevel", "Leistung"])

        tmp["Stress_Status"] = np.where(tmp["Stresslevel"] >= stress_threshold, "Stress", "Kein Stress")

        compare_df = tmp.groupby("Stress_Status", as_index=False)["Leistung"].agg(Ø_Leistung="mean", n="count")
        order = ["Kein Stress", "Stress"]
        compare_df["Stress_Status"] = pd.Categorical(compare_df["Stress_Status"], categories=order, ordered=True)
        compare_df = compare_df.sort_values("Stress_Status")

        fig_cmp = px.bar(compare_df, x="Stress_Status", y="Ø_Leistung", text=compare_df["Ø_Leistung"].round(2), template="gridon")
        fig_cmp.update_layout(xaxis_title="Gruppe", yaxis_title="Ø Leistung")
        fig_cmp.update_yaxes(range=[0.5, 10.5], tickmode="linear", tick0=1, dtick=1)

        chart_with_data(fig_cmp, compare_df, "Daten anzeigen")

st.divider()

# ====================================
# GRAPH 3 — LINE (Time Series)
# (nur anzeigen, wenn KEIN einzelnes Semester gefiltert ist)
# ====================================

if semester == "Alle":

    st.subheader("Stressverlauf über Studium")

    line_df = (
        filtered_df
        .groupby("Semester", as_index=False)["Stresslevel"]
        .mean()
    )

    all_semesters = pd.DataFrame({"Semester": list(range(1, 11))})
    line_df = all_semesters.merge(line_df, on="Semester", how="left")
    line_df["Stresslevel"] = line_df["Stresslevel"].interpolate()
    line_df["Semester"] = pd.to_numeric(line_df["Semester"], errors="coerce")

    fig3 = px.line(
        line_df,
        x="Semester",
        y="Stresslevel",
        markers=True,
        template="gridon"
    )

    fig3.update_xaxes(
        tickmode="array",
        tickvals=list(range(1, 11)),
        ticktext=[str(i) for i in range(1, 11)],
        range=[1, 10]
    )

    chart_with_data(fig3, line_df, "Daten anzeigen")

# ====================================
# GRAPH 4 — LINKS (Semesterphasen) / RECHTS (Stressauslöser)
# ====================================
c3, c4 = st.columns(2)

with c3:
    st.subheader("Stressverlauf über das Semester")

    if "Semesterphase" not in filtered_df.columns:
        st.error("Spalte 'Semesterphase' fehlt in der CSV. Bitte CSV neu generieren und neu laden.")
    else:
        phase_order = ["früh", "mitte", "spät"]

        phase_df = (
            filtered_df
            .groupby("Semesterphase", as_index=False)["Stresslevel"]
            .mean()
        )

        # Reihenfolge + alle 3 Phasen erzwingen (auch wenn eine mal fehlen sollte)
        phase_df["Semesterphase"] = pd.Categorical(
            phase_df["Semesterphase"],
            categories=phase_order,
            ordered=True
        )
        phase_df = phase_df.sort_values("Semesterphase")

        all_phases = pd.DataFrame({"Semesterphase": phase_order})
        phase_df = all_phases.merge(phase_df, on="Semesterphase", how="left")
        phase_df["Stresslevel"] = phase_df["Stresslevel"].interpolate()

        fig_phase = px.line(
            phase_df,
            x="Semesterphase",
            y="Stresslevel",
            markers=True,
            template="gridon"
        )
        fig_phase.update_layout(
            xaxis_title="Phase des Semesters",
            yaxis_title="Ø Stresslevel"
        )

        chart_with_data(fig_phase, phase_df, "Daten anzeigen")

with c4:
    st.subheader("Häufigste Stressauslöser")

    trigger_df = filtered_df["Stressfaktor"].value_counts().reset_index()
    trigger_df.columns = ["Stressauslöser", "Anzahl"]

    fig_trigger = px.bar(trigger_df, x="Stressauslöser", y="Anzahl", text="Anzahl", template="gridon")
    fig_trigger.update_layout(xaxis_title="Stressauslöser", yaxis_title="Anzahl Studierender")

    chart_with_data(fig_trigger, trigger_df, "Daten anzeigen")

st.divider()

# ====================================
# GRAPH — STRESS VS SCHLAF
# ====================================
st.subheader("Stress in Abhängigkeit von Schlafdauer")

df_sleep = filtered_df[["Schlafstunden", "Stresslevel"]].copy()
df_sleep["Schlafstunden"] = pd.to_numeric(df_sleep["Schlafstunden"], errors="coerce")
df_sleep["Stresslevel"] = pd.to_numeric(df_sleep["Stresslevel"], errors="coerce")
df_sleep = df_sleep.dropna()

df_sleep["Schlaf_bin"] = (df_sleep["Schlafstunden"] * 2).round() / 2
df_sleep = df_sleep[(df_sleep["Schlaf_bin"] >= 3.0) & (df_sleep["Schlaf_bin"] <= 9.0)]

bar_df = df_sleep.groupby("Schlaf_bin", as_index=False)["Stresslevel"].mean()
bar_df["Stresslevel"] = bar_df["Stresslevel"].clip(lower=2, upper=9)

fig_sleep = px.bar(bar_df, x="Schlaf_bin", y="Stresslevel", template="gridon")
fig_sleep.update_layout(xaxis_title="Schlafdauer (Stunden)", yaxis_title="Ø Stresslevel")

chart_with_data(fig_sleep, bar_df, "Daten anzeigen")

st.divider()


# ====================================
# COPING — 2 PIEs
# ====================================
p1, p2 = st.columns(2)

with p1:
    st.subheader("Kurzzeit-Coping (akut)")
    c_short = filtered_df["Coping_Kurzzeit"].value_counts().reset_index()
    c_short.columns = ["Strategie", "Anzahl"]

    fig_short = px.pie(c_short, names="Strategie", values="Anzahl")
    fig_short.update_traces(textposition="inside", textinfo="percent+label")
    fig_short.update_layout(legend_title="Kurzzeit")

    chart_with_data(fig_short, c_short, "Daten anzeigen")

with p2:
    st.subheader("Langzeit-Coping (nachhaltig)")
    c_long = filtered_df["Coping_Langzeit"].value_counts().reset_index()
    c_long.columns = ["Strategie", "Anzahl"]

    fig_long = px.pie(c_long, names="Strategie", values="Anzahl")
    fig_long.update_traces(textposition="inside", textinfo="percent+label")
    fig_long.update_layout(legend_title="Langzeit")

    chart_with_data(fig_long, c_long, "Daten anzeigen")

st.divider()

# ====================================
# 11. SYNTHESE: High-Stress vs Low-Stress
# ====================================

st.subheader("Synthese: Was trennt High-Stress von Low-Stress?")

if len(filtered_df) == 0:
    st.info("Keine Daten nach Filterauswahl.")
else:
    STRESS_COL = "Stresslevel"
    SLEEP_COL = "Schlafstunden"
    PERF_COL = "Leistung"  # muss in CSV vorhanden sein
    COPING_S = "Coping_Kurzzeit"
    COPING_L = "Coping_Langzeit"

    tmp = filtered_df.copy()
    tmp[STRESS_COL] = pd.to_numeric(tmp[STRESS_COL], errors="coerce")
    tmp[SLEEP_COL] = pd.to_numeric(tmp[SLEEP_COL], errors="coerce")
    if PERF_COL in tmp.columns:
        tmp[PERF_COL] = pd.to_numeric(tmp[PERF_COL], errors="coerce")

    tmp = tmp.dropna(subset=[STRESS_COL, SLEEP_COL])

    tmp["Stressgruppe_binary"] = np.where(tmp[STRESS_COL] >= stress_threshold, "High-Stress", "Low-Stress")

    # Kennzahlenvergleich
    agg_dict = {
        SLEEP_COL: "mean",
        STRESS_COL: "mean",
    }
    if PERF_COL in tmp.columns:
        agg_dict[PERF_COL] = "mean"

    compare = (
        tmp.groupby("Stressgruppe_binary", as_index=False)
        .agg(agg_dict)
        .rename(columns={
            SLEEP_COL: "Ø Schlaf (h)",
            STRESS_COL: "Ø Stresslevel",
            PERF_COL: "Ø Leistung" if PERF_COL in tmp.columns else PERF_COL
        })
    )

    # Reihenfolge fix
    order = ["Low-Stress", "High-Stress"]
    compare["Stressgruppe_binary"] = pd.Categorical(compare["Stressgruppe_binary"], categories=order, ordered=True)
    compare = compare.sort_values("Stressgruppe_binary")

    # Plot: Schlaf & Leistung (nebeneinander)
    a, b = st.columns(2)

    with a:
        st.markdown("*Definition: Low-Stress vs High-Stress*")

        # Daten für einen durchgehenden Balken 1–10
        scale_df = pd.DataFrame({"x0": [1], "x1": [10], "y": ["Stresslevel (1–10)"]})

        fig_def = px.bar(
            pd.DataFrame({"Label": ["Stresslevel (1–10)"], "Wert": [10]}),
            x="Wert",
            y="Label",
            orientation="h",
            template="gridon"
        )

        # Achse 1..10
        fig_def.update_xaxes(
            range=[0.5, 10.5],
            tickmode="array",
            tickvals=list(range(1, 11)),
            ticktext=[str(i) for i in range(1, 11)],
            title="Stresslevel"
        )
        fig_def.update_yaxes(title="")

        # Schwellenlinie (ab hier High-Stress)
        fig_def.add_vline(
         x=stress_threshold,
         line_width=3,
            line_dash="dash"
        )

        # Labels Low/High als Annotationen
        fig_def.add_annotation(
            x=(1 + (stress_threshold - 1)) / 2,
            y=0,
            text=f"Low: 1–{stress_threshold-1}",
            showarrow=False,
            yshift=18
        )
        fig_def.add_annotation(
            x=(stress_threshold + 10) / 2,
            y=0,
            text=f"High: {stress_threshold}–10",
            showarrow=False,
            yshift=18
        )
        fig_def.add_annotation(
            x=stress_threshold,
            y=0,
            text=f"Schwelle = {stress_threshold}",
            showarrow=False,
            yshift=-22
        )

        fig_def.update_layout(showlegend=False)

        # kleine Tabelle im Expander (Definition)
        def_df = pd.DataFrame({
            "Gruppe": ["Low-Stress", "High-Stress"],
            "Stresslevel-Bereich": [f"1–{stress_threshold-1}", f"{stress_threshold}–10"],
            "Regel": [f"Stresslevel < {stress_threshold}", f"Stresslevel ≥ {stress_threshold}"]
        })

        chart_with_data(fig_def, def_df, "Definition anzeigen")

    with b:
        if PERF_COL in tmp.columns:
            fig_perf_cmp = px.bar(
                compare,
                x="Stressgruppe_binary",
                y="Ø Leistung",
                text=compare["Ø Leistung"].round(2),
                template="gridon"
            )
            fig_perf_cmp.update_layout(xaxis_title="", yaxis_title="Ø Leistung")
            fig_perf_cmp.update_yaxes(range=[0.5, 10.5], tickmode="linear", tick0=1, dtick=1)
            chart_with_data(fig_perf_cmp, compare[["Stressgruppe_binary", "Ø Leistung"]], "Daten anzeigen")
        else:
            st.info("Spalte 'Leistung' fehlt – Leistungsvergleich wird nicht angezeigt.")

    # Coping-Top3 Vergleich (Kurzzeit)
    st.subheader("Coping (Kurzzeit): Top-Strategien nach Stressgruppe")
    coping_cmp = (
        tmp.groupby(["Stressgruppe_binary", COPING_S], as_index=False)
        .size()
        .rename(columns={"size": "Anzahl"})
    )
    # Top 3 pro Gruppe
    coping_top = (
        coping_cmp.sort_values(["Stressgruppe_binary", "Anzahl"], ascending=[True, False])
        .groupby("Stressgruppe_binary")
        .head(3)
    )

    fig_coping = px.bar(
        coping_top,
        x=COPING_S,
        y="Anzahl",
        color="Stressgruppe_binary",
        barmode="group",
        template="gridon"
    )
    fig_coping.update_layout(xaxis_title="Kurzzeit-Coping", yaxis_title="Anzahl")
    chart_with_data(fig_coping, coping_top, "Daten anzeigen")

    st.markdown(
        """
*Story-Message:* Hoher Stress ist nicht zufällig, sondern hängt systematisch mit Schlaf, zeitlichen Mustern und Bewältigungsstrategien zusammen.
        """
    )

st.divider()

# ====================================
# 12. TAKEAWAYS (Footer)
# ====================================

st.subheader("Takeaways")

if len(filtered_df) == 0:
    st.info("Keine Daten nach Filterauswahl.")
else:
    stress_rate = (filtered_df["Stresslevel"] >= stress_threshold).mean() * 100
    avg_sleep = pd.to_numeric(filtered_df["Schlafstunden"], errors="coerce").mean()

    bullets = [
        f"Stress betrifft einen großen Teil der Studierenden (gestresst: {stress_rate:.1f}%).",
        "Hoher Stress geht im Schnitt mit geringerer Leistung einher.",
        "Stress folgt zeitlichen Mustern über das Studium und innerhalb des Semesters.",
        f"Schlaf ist eine zentrale Stellschraube (Ø Schlaf: {avg_sleep:.2f} h).",
        "Bewältigungsstrategien unterscheiden sich zwischen High- und Low-Stress."
    ]

    for b in bullets:
        st.write("• " + b)

# ====================================
# SUMMARY TABLE
# ====================================
st.subheader("Stichprobe der Daten")
with st.expander("Daten anzeigen"):
    st.dataframe(filtered_df.head(20))

# ====================================
# DOWNLOAD
# ====================================
csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button("Download Data", csv, "Stress_Studierende_dashboard.csv", "text/csv")