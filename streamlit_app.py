import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import base64

# App-Konfiguration
st.set_page_config(
    page_title="Strukturkurve Europäischer Survey-Inflationserwartungen",
    page_icon="📈",
    layout="wide"
)

# Länder-Konfiguration
COUNTRIES = {
    'Deutschland': 'de',
    'Spanien': 'es', 
    'Eurozone': 'ez',
    'Frankreich': 'fr',
    'Italien': 'it',
    'Niederlande': 'nl'
}

@st.cache_data
def load_data(country_code):
    """Lädt und bereitet die Daten für das gewählte Land vor"""
    try:
        # Pfad zur Excel-Datei
        file_path = f"data/{country_code}/FittedTermStructure.xlsx"
        
        # Excel-Datei einlesen
        df = pd.read_excel(file_path)
        
        # Spaltennamen bereinigen - Leerzeichen entfernen
        df.columns = [col.replace(' ', '') for col in df.columns]

        # Alle numerischen Spalten auf 3 Nachkommastellen runden
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].round(3)
        
        # Zeit-Spalte verarbeiten
        if 'Time' in df.columns:
            df['Time'] = pd.to_datetime(df['Time'])
        elif df.columns[0] not in ['pi_1q', 'pi_2q']:
            df = df.rename(columns={df.columns[0]: 'Time'})
            df['Time'] = pd.to_datetime(df['Time'])
        
        # explizit nach datum (aufsteigend) sortieren
        df = df.sort_values('Time').reset_index(drop=True)
        
        return df
        
    except FileNotFoundError:
        st.error(f"Datei nicht gefunden: {file_path}")
        st.info("Verwende Beispiel-Daten für Demo-Zwecke")
        return load_sample_data()
    except Exception as e:
        st.error(f"Fehler beim Laden der Daten: {str(e)}")
        st.info("Verwende Beispiel-Daten für Demo-Zwecke")
        return load_sample_data()

def load_sample_data():
    """Lädt Beispiel-Daten falls echte Daten nicht verfügbar"""
    quarters = []
    
    for year in range(1989, 2026):
        for quarter in [3, 6, 9, 12]:
            if year == 1989 and quarter < 12:
                continue
            month = quarter if quarter != 12 else 12
            day = 31 if quarter == 12 else 30
            if quarter == 6:
                day = 30
            elif quarter == 3:
                day = 31
            elif quarter == 9:
                day = 30
            
            date_str = f"{day:02d}.{month:02d}.{year}"
            quarters.append(date_str)
    
    np.random.seed(42)
    n_quarters = len(quarters)
    data = {'Time': quarters}
    
    for q in range(1, 41):
        base_trend = 2.0 + 0.5 * np.sin(np.linspace(0, 4*np.pi, n_quarters))
        horizon_adjustment = (q - 1) * 0.01
        noise = np.random.normal(0, 0.2, n_quarters)
        values = base_trend + horizon_adjustment + noise
        values = np.maximum(values, 0.5)
        data[f'pi_{q}q'] = values
    
    df = pd.DataFrame(data)
    df['Time'] = pd.to_datetime(df['Time'], format='%d.%m.%Y')
    return df

def format_quarter(date):
    """Formatiert Datum als YYYYQX"""
    year = date.year
    month = date.month
    if month in [1, 2, 3]:
        quarter = 1
    elif month in [4, 5, 6]:
        quarter = 2
    elif month in [7, 8, 9]:
        quarter = 3
    else:
        quarter = 4
    return f"{year}Q{quarter}"

def get_global_y_range(df):
    """Berechnet globale Min/Max-Werte für einheitliche Skalierung"""
    horizons_cols = [col for col in df.columns if col.startswith('pi_')]
    all_values = []
    for col in horizons_cols:
        all_values.extend(df[col].dropna().tolist())
    
    if all_values:
        global_min = min(all_values)
        global_max = max(all_values)
        return [global_min - 0.2, global_max + 0.2]
    else:
        return [0, 5]

def create_timeseries_overview_chart(df):
    """Erstellt Zeitreihen-Plot für ausgewählte Inflationserwartungs-Horizonte"""
    fig = go.Figure()
    
    y_range = get_global_y_range(df)
    
    # Horizonte ohne Leerzeichen (da diese beim Laden entfernt wurden)
    selected_horizons = [
    ('pi_1q', '1 Quartal', '#000080'),    # Dunkelblau
    ('pi_2q', '2 Quartale', '#0000FF'),   # Blau
    ('pi_3q', '3 Quartale', '#0080FF'),   # Hellblau
    ('pi_4q', '4 Quartale', '#00FFFF'),   # Cyan
    ('pi_6q', '6 Quartale', '#00FF80'),   # Grün-Cyan
    ('pi_8q', '8 Quartale', '#00FF00'),   # Grün
    ('pi_12q', '12 Quartale', '#80FF00'), # Gelbgrün
    ('pi_16q', '16 Quartale', '#FFFF00'), # Gelb
    ('pi_20q', '20 Quartale', '#FF8000'), # Orange
    ('pi_30q', '30 Quartale', '#FF4000'), # Rot-Orange
    ('pi_40q', '40 Quartale', '#FF0000')  # Rot
    ]
    
    available_cols = [col for col in df.columns if col.startswith('pi_')]
    
    for horizon_col, label, color in selected_horizons:
        if horizon_col in available_cols:
            fig.add_trace(go.Scatter(
                x=df['Time'],
                y=df[horizon_col],
                mode='lines',
                name=label,
                line=dict(color=color, width=2),
                hovertemplate=f'%{{x}}<br>{label}: %{{y:.3f}}%<extra></extra>'
            ))
    
    # fig.update_layout(
    #     title="Evolution der Inflationserwartungen über Zeit",
    #     xaxis_title="Zeit",
    #     yaxis_title="Inflationserwartungen (% p.a.)",
    #     yaxis=dict(range=y_range),
    #     hovermode='x unified',
    #     height=600,
    #     legend=dict(
    #         orientation="h",
    #         yanchor="bottom",
    #         y=1.02,
    #         xanchor="right",
    #         x=1
    #     )
    # )
    
    return fig

def prepare_curve_data(df):
    """Bereitet Daten für Strukturkurven vor"""
    horizons = [col for col in df.columns if col.startswith('pi_')]
    horizon_values = [int(col.split('_')[1][:-1]) for col in horizons]
    
    curves_data = []
    for idx, row in df.iterrows():
        curve_data = {
            'date': row['Time'],
            'quarter_label': format_quarter(row['Time']),
            'horizons': horizon_values,
            'values': [row[col] for col in horizons]
        }
        curves_data.append(curve_data)
    
    return curves_data

def create_comparison_chart(df, selected_dates, use_fixed_scale=True):
    """Erstellt Vergleichschart für mehrere Zeitpunkte"""
    fig = go.Figure()
    
    horizons = [col for col in df.columns if col.startswith('pi_')]
    horizon_values = [int(col.split('_')[1][:-1]) for col in horizons]
    
    colors = px.colors.qualitative.Set1
    
    for i, date in enumerate(selected_dates):
        row = df[df['Time'] == date].iloc[0]
        values = [row[col] for col in horizons]
        quarter_label = format_quarter(date)
        
        fig.add_trace(go.Scatter(
            x=horizon_values,
            y=values,
            mode='lines+markers',
            name=quarter_label,
            line=dict(color=colors[i % len(colors)], width=2),
            marker=dict(size=6)
        ))
    
    layout_kwargs = {
        'title': "Vergleich der Inflationserwartungen-Strukturkurven",
        'xaxis_title': "Horizont (Quartale)",
        'yaxis_title': "Inflationserwartungen (% p.a.)",
        'hovermode': 'x unified',
        'height': 500
    }
    
    if use_fixed_scale:
        layout_kwargs['yaxis'] = dict(range=get_global_y_range(df))
    
    fig.update_layout(**layout_kwargs)
    return fig

def create_evolution_chart(curves_data, selected_idx, df, use_fixed_scale=True):
    """Evolution-Chart mit einer Strukturkurve"""
    fig = go.Figure()
    
    current_curve = curves_data[selected_idx]
    fig.add_trace(
        go.Scatter(
            x=current_curve['horizons'],
            y=current_curve['values'],
            mode='lines+markers',
            name=f"Strukturkurve {current_curve['quarter_label']}",
            line=dict(color='darkblue', width=3),
            marker=dict(size=8, color='darkblue')
        )
    )
    
    layout_kwargs = {
        'title': f"Strukturkurve - {current_curve['quarter_label']}",
        'xaxis_title': "Horizont (Quartale)",
        'yaxis_title': "Inflationserwartungen (% p.a.)",
        'height': 500,
        'hovermode': 'x'
    }
    
    if use_fixed_scale:
        layout_kwargs['yaxis'] = dict(range=get_global_y_range(df))
    
    fig.update_layout(**layout_kwargs)
    return fig

def download_data_as_csv(df):
    """Erstellt Download-Link für CSV"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="inflationserwartungen.csv">💾 Daten als CSV herunterladen</a>'
    return href

def download_selected_data_as_csv(df, selected_dates):
    """Erstellt Download-Link für nur die ausgewählten Quartale"""
    # Filtere nur die ausgewählten Zeilen
    filtered_df = df[df['Time'].isin(selected_dates)].copy()
    
    csv = filtered_df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="ausgewaehlte_quartale.csv">💾 Chart-Daten als CSV herunterladen</a>'
    return href

# Hauptanwendung
def main():
    st.title("Strukturkurve Europäischer Survey-Inflationserwartungen")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.header("Einstellungen")
    selected_country = st.sidebar.selectbox(
        "Land auswählen",
        list(COUNTRIES.keys()),
        index=2,  # Eurozone als Default
        help="Wählen Sie das Land für die Analyse"
    )
    
    country_code = COUNTRIES[selected_country]
    
    # Daten laden
    df = load_data(country_code)
    curves_data = prepare_curve_data(df)
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📈 Übersicht", "🔍 Strukturkurven Vergleich", "🎬 Evolution der Kurve"])
    
    with tab1:
        st.header("Gesamtübersicht der Strukturkurve")
        
        # Chart
        fig_timeseries = create_timeseries_overview_chart(df)
        st.plotly_chart(fig_timeseries, use_container_width=True)
        
        # Downloads UNTER dem Chart
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.markdown(download_data_as_csv(df), unsafe_allow_html=True)
        
    
    with tab2:
        st.header("Vergleich mehrerer Zeitpunkte")
        
        quarter_options = [(row['Time'], format_quarter(row['Time'])) for _, row in df.iterrows()]
        quarter_labels = [label for _, label in quarter_options]
        
        default_selection = quarter_labels[-3:] if len(quarter_labels) >= 3 else quarter_labels
        
        selected_quarter_labels = st.multiselect(
            "Wählen Sie Quartale zum Vergleichen:",
            options=quarter_labels,
            default=default_selection,
            help="Wählen Sie bis zu 8 Quartale für den Vergleich"
        )
        
        use_fixed_y_axis = st.checkbox(
            "Feste Y-Achse verwenden",
            value=False,
            help="Wenn aktiviert, wird dieselbe Y-Achsen-Skalierung wie in der Übersicht verwendet"
        )
        
        if selected_quarter_labels:
            selected_dates = []
            for label in selected_quarter_labels:
                for date, qlabel in quarter_options:
                    if qlabel == label:
                        selected_dates.append(date)
                        break
            
            fig1 = create_comparison_chart(df, selected_dates, use_fixed_y_axis)
            st.plotly_chart(fig1, use_container_width=True)
        
             # Downloads UNTER dem Chart
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                st.markdown(download_selected_data_as_csv(df, selected_dates), unsafe_allow_html=True)
    
    with tab3:
        st.header("Evolution der Strukturkurve")
        
        quarter_labels_dropdown = [curves_data[i]['quarter_label'] for i in range(len(curves_data))]
        
        #selected_quarter_label = st.selectbox(
        #    "Wählen Sie ein Quartal:",
        #    options=quarter_labels_dropdown,
        #    index=len(quarter_labels_dropdown)-1,
        #    help="Wählen Sie das Quartal für die Strukturkurve"
        #)

        selected_quarter_label = st.select_slider(
        "Wählen Sie ein Quartal:",
        options=quarter_labels_dropdown,
        value=quarter_labels_dropdown[-1],
        help="Verwenden Sie den Slider, um durch die Quartale zu navigieren"
        )

        # Index für das ausgewählte Quartal finden
        selected_quarter_idx = quarter_labels_dropdown.index(selected_quarter_label)
        
        use_fixed_y_axis_evolution = st.checkbox(
            "Feste Y-Achse verwenden",
            value=False,
            key="fixed_y_evolution",
            help="Wenn aktiviert, wird dieselbe Y-Achsen-Skalierung wie in der Übersicht verwendet"
        )
        
        selected_quarter_idx = quarter_labels_dropdown.index(selected_quarter_label)
        
        fig2 = create_evolution_chart(curves_data, selected_quarter_idx, df, use_fixed_y_axis_evolution)
        st.plotly_chart(fig2, use_container_width=True)
        
        
        # Details zum ausgewählten Quartal - nur Metriken
        st.subheader("Details zum ausgewählten Quartal")
        current_curve = curves_data[selected_quarter_idx]
        
        col1, col2, col3 = st.columns(3)
        values = current_curve['values']
        
        with col1:
            st.metric("Kurzfristig (1Q)", f"{values[0]:.3f}%")
        with col2:
            st.metric("Mittelfristig (8Q)", f"{values[7]:.3f}%" if len(values) > 7 else f"{values[-1]:.3f}%")
        with col3:
            st.metric("Langfristig (20Q)", f"{values[19]:.3f}%" if len(values) > 19 else f"{values[-1]:.3f}%")

if __name__ == "__main__":
    main()