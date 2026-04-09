import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import base64

# App configuration
st.set_page_config(
    page_title="Term Structure of European Survey Inflation Expectations",
    page_icon="📈",
    layout="wide"
)

# Country configuration
COUNTRIES = {
    'Germany': 'de',
    'Spain': 'es', 
    'Euro Area': 'ez',
    'France': 'fr',
    'Italy': 'it',
    'Netherlands': 'nl'
}

@st.cache_data
def load_data(country_code):
    """Loads and prepares data for the selected country"""
    try:
        file_path = f"data/{country_code}/FittedTermStructure.xlsx"
        
        df = pd.read_excel(file_path)
        
        df.columns = [col.replace(' ', '') for col in df.columns]

        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].round(3)
        
        if 'Time' in df.columns:
            df['Time'] = pd.to_datetime(df['Time'])
        elif df.columns[0] not in ['pi_1q', 'pi_2q']:
            df = df.rename(columns={df.columns[0]: 'Time'})
            df['Time'] = pd.to_datetime(df['Time'])
        
        df = df.sort_values('Time').reset_index(drop=True)
        
        return df
        
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        st.info("Using sample data for demo purposes")
        return load_sample_data()
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info("Using sample data for demo purposes")
        return load_sample_data()

def load_sample_data():
    """Loads sample data if real data is not available"""
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
    """Formats date as YYYYQX"""
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
    """Calculates global min/max values for consistent scaling"""
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
    """Creates time series plot for selected inflation expectation horizons"""
    fig = go.Figure()
    
    y_range = get_global_y_range(df)
    
    selected_horizons = [
    ('pi_1q', '1 Quarter', '#000080'),
    ('pi_2q', '2 Quarters', '#0000FF'),
    ('pi_3q', '3 Quarters', '#0080FF'),
    ('pi_4q', '4 Quarters', '#00FFFF'),
    ('pi_6q', '6 Quarters', '#00FF80'),
    ('pi_8q', '8 Quarters', '#00FF00'),
    ('pi_12q', '12 Quarters', '#80FF00'),
    ('pi_16q', '16 Quarters', '#FFFF00'),
    ('pi_20q', '20 Quarters', '#FF8000'),
    ('pi_30q', '30 Quarters', '#FF4000'),
    ('pi_40q', '40 Quarters', '#FF0000')
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
    
    fig.update_layout(
        title="Evolution of Inflation Expectations Over Time",
        xaxis_title="Time",
        yaxis_title="Inflation Expectations (% p.a.)",
        yaxis=dict(range=y_range),
        hovermode='x unified',
        height=600,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def prepare_curve_data(df):
    """Prepares data for term structure curves"""
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
    """Creates comparison chart for multiple time points"""
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
        'title': "Comparison of Inflation Expectation Term Structures",
        'xaxis_title': "Horizon (Quarters)",
        'yaxis_title': "Inflation Expectations (% p.a.)",
        'hovermode': 'x unified',
        'height': 500
    }
    
    if use_fixed_scale:
        layout_kwargs['yaxis'] = dict(range=get_global_y_range(df))
    
    fig.update_layout(**layout_kwargs)
    return fig

def create_evolution_chart(curves_data, selected_idx, df, use_fixed_scale=True):
    """Evolution chart with a single term structure curve"""
    fig = go.Figure()
    
    current_curve = curves_data[selected_idx]
    fig.add_trace(
        go.Scatter(
            x=current_curve['horizons'],
            y=current_curve['values'],
            mode='lines+markers',
            name=f"Term Structure {current_curve['quarter_label']}",
            line=dict(color='darkblue', width=3),
            marker=dict(size=8, color='darkblue')
        )
    )
    
    layout_kwargs = {
        'title': f"Term Structure - {current_curve['quarter_label']}",
        'xaxis_title': "Horizon (Quarters)",
        'yaxis_title': "Inflation Expectations (% p.a.)",
        'height': 500,
        'hovermode': 'x'
    }
    
    if use_fixed_scale:
        layout_kwargs['yaxis'] = dict(range=get_global_y_range(df))
    
    fig.update_layout(**layout_kwargs)
    return fig

def download_data_as_csv(df):
    """Creates download link for CSV"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="inflation_expectations.csv">💾 Download data as CSV</a>'
    return href

def download_selected_data_as_csv(df, selected_dates):
    """Creates download link for selected quarters only"""
    filtered_df = df[df['Time'].isin(selected_dates)].copy()
    
    csv = filtered_df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="selected_quarters.csv">💾 Download chart data as CSV</a>'
    return href

# Main application
def main():
    st.title("Term Structure of European Survey Inflation Expectations")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.header("Settings")
    selected_country = st.sidebar.selectbox(
        "Select country",
        list(COUNTRIES.keys()),
        index=2,  # Euro Area as default
        help="Select the country for analysis"
    )
    
    country_code = COUNTRIES[selected_country]
    
    # Load data
    df = load_data(country_code)
    curves_data = prepare_curve_data(df)
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📈 Overview", "🔍 Term Structure Comparison", "🎬 Curve Evolution"])
    
    with tab1:
        st.header("Overview of the Term Structure")
        
        fig_timeseries = create_timeseries_overview_chart(df)
        st.plotly_chart(fig_timeseries, use_container_width=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.markdown(download_data_as_csv(df), unsafe_allow_html=True)
        
    
    with tab2:
        st.header("Comparison of Multiple Time Points")
        
        quarter_options = [(row['Time'], format_quarter(row['Time'])) for _, row in df.iterrows()]
        quarter_labels = [label for _, label in quarter_options]
        
        default_selection = quarter_labels[-3:] if len(quarter_labels) >= 3 else quarter_labels
        
        selected_quarter_labels = st.multiselect(
            "Select quarters to compare:",
            options=quarter_labels,
            default=default_selection,
            help="Select up to 8 quarters for comparison"
        )
        
        use_fixed_y_axis = st.checkbox(
            "Use fixed Y-axis",
            value=False,
            help="If enabled, uses the same Y-axis scale as the overview chart"
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
        
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                st.markdown(download_selected_data_as_csv(df, selected_dates), unsafe_allow_html=True)
    
    with tab3:
        st.header("Evolution of the Term Structure")
        
        quarter_labels_dropdown = [curves_data[i]['quarter_label'] for i in range(len(curves_data))]

        selected_quarter_label = st.select_slider(
            "Select a quarter:",
            options=quarter_labels_dropdown,
            value=quarter_labels_dropdown[-1],
            help="Use the slider to navigate through quarters"
        )

        selected_quarter_idx = quarter_labels_dropdown.index(selected_quarter_label)
        
        use_fixed_y_axis_evolution = st.checkbox(
            "Use fixed Y-axis",
            value=False,
            key="fixed_y_evolution",
            help="If enabled, uses the same Y-axis scale as the overview chart"
        )
        
        selected_quarter_idx = quarter_labels_dropdown.index(selected_quarter_label)
        
        fig2 = create_evolution_chart(curves_data, selected_quarter_idx, df, use_fixed_y_axis_evolution)
        st.plotly_chart(fig2, use_container_width=True)
        
        st.subheader("Details for Selected Quarter")
        current_curve = curves_data[selected_quarter_idx]
        
        col1, col2, col3 = st.columns(3)
        values = current_curve['values']
        
        with col1:
            st.metric("Short-term (1Q)", f"{values[0]:.3f}%")
        with col2:
            st.metric("Medium-term (8Q)", f"{values[7]:.3f}%" if len(values) > 7 else f"{values[-1]:.3f}%")
        with col3:
            st.metric("Long-term (20Q)", f"{values[19]:.3f}%" if len(values) > 19 else f"{values[-1]:.3f}%")

if __name__ == "__main__":
    main()
