import altair as alt
import datetime
import numpy as np
import pandas as pd
import streamlit as st
from string import capwords
import textwrap
import xarray as xr

from maps import plot_maps
from utils import INTRO, fluxnames, convert_ch4_gwp, convert_n2o_gwp, gwp_vars
from report import create_report



@st.cache(allow_output_mutation=True)
def load_raw_data_awd():
    return xr.open_dataset('../data/demo1_philippines/default_awd_hr_200_nobund_daily_ts_ha.nc')

@st.cache(allow_output_mutation=True)
def load_raw_data_cf():
    return xr.open_dataset('../data/demo1_philippines/default_cf_hr_200_nobund_daily_ts_ha.nc')

@st.cache(allow_output_mutation=True)
def load_raw_data_awd_gridcell():
    return xr.open_dataset('../data/demo1_philippines/default_awd_hr_200_nobund_daily_ts_gridcell.nc')

@st.cache(allow_output_mutation=True)
def load_raw_data_cf_gridcell():
    return xr.open_dataset('../data/demo1_philippines/default_cf_hr_200_nobund_daily_ts_gridcell.nc')

def identify_index_col(df):
    for c in df.columns.values:
        if str(c).lower() in ['time', 'date', 'year']:
            return str(c)
    return None

def process_df(df, vars):
    df_ = df.reset_index()[vars] if vars else df.reset_index()
    if vars is None:
        vars = list(df.columns.values)

    # rename columns
    for v in vars:
        df_ = df_.rename({v: fluxnames.get(v)}, axis=1)

    index_col_ = identify_index_col(df_)
    df_ = df_.melt(index_col_, var_name='variable', value_name='value')
    return (index_col_, df_)

def line_plot(df, vars=None, units=None):
    units_ = units if units else '[kg yr⁻¹]'
    index_, df_ = process_df(df, vars)
    c = alt.Chart(df_).mark_line().encode(
            alt.X(f'{index_}:T', title=''),
            alt.Y('value:Q', title=f'Flux {units_}'), 
            alt.Color('variable:N', legend=alt.Legend(title='')), 
        ).configure_axis(
            grid=False
        )
    st.altair_chart(c)

def bar_plot(df, vars=None, units=None):
    units_ = units if units else '[kg yr⁻¹]'
    index_, df_ = process_df(df, vars)
    df_['year'] = df_[index_].dt.year
    c = alt.Chart(df_).mark_bar().encode(
            alt.X('year:O', title=''),
            alt.Y('value:Q', title=f'Flux {units_}'), 
            alt.Color('variable:N', legend=alt.Legend(title='')), 
        ).configure_axis(
            grid=False
        )
    st.altair_chart(c)    


def main():
    st.title('Data explorer for LandscapeDNDC Philippines sims')

    st.sidebar.header("Options")
    st.sidebar.subheader("General")

    show_intro = st.sidebar.checkbox("Show intro", value=True)
    show_code = st.sidebar.checkbox("Show code", value=False)
    show_report = st.sidebar.checkbox("Show report & maps", value=False)

    if show_intro:
        st.markdown(INTRO)

    st.markdown("""\
        App created by
        [Christian Werner (christian.werner@kit.edu)](https://www.christianwerner.net)\n""")

    if show_code:
        st.header("The streamlit code of this demo")
        st.markdown("Check out the full source code of this app at https://www.github.com/cwerner/adl01_streamlit-demo.")
        st.code(open(__file__).read())


    ds_awd = load_raw_data_awd()
    ds_cf  = load_raw_data_cf()

    ds_awd_gc = load_raw_data_awd_gridcell()
    ds_cf_gc  = load_raw_data_cf_gridcell()

    # some simple altair plot
    fluxes = [v for v in ds_awd.data_vars.keys() if 'dN_' in v] + \
            [v for v in ds_awd.data_vars.keys() if 'dC_' in v]

    # filter some vars from data source
    fluxes = [f for f in fluxes if f not in ['dN_litter','dN_fertilizer','dC_bud']]

    st.header("Data exploration")

    only_ghg_vars = st.checkbox('Only GHG emissions (values converted to GWP [1])')
    if only_ghg_vars:
        fluxes = gwp_vars
        default_sel = fluxes
    else:
        default_sel = ['dN_n2o_emis']

    sel_vars = st.empty()
    vars = sel_vars.multiselect("Pick one or multiple variables (click into field for selection)", 
                                fluxes, 
                                default=default_sel,
                                format_func=fluxnames.get, key='a')

    # hack to prevent downstream code to crash if no variables are selected
    if len(vars) == 0:
        return

    if (('dC_ch4_emis' in vars) and len(vars) > 1 and only_ghg_vars == False):
        st.warning("⚠️ C and N variables in same plot. Tick option above... Only N-based fluxes shown.")
        vars.remove('dC_ch4_emis')

    # sidebar options
    st.sidebar.subheader("Data selection")
    sel_timestep = st.sidebar.radio("Show daily or annual data", ['daily', 'annual'])

    # data smoothing
    sel_smooth = st.sidebar.empty() 
    smooth_slider = st.sidebar.empty()
    smooth = sel_smooth.checkbox("Smooth (daily) data")
    if smooth:
        smooth_rate = smooth_slider.slider("smoothing rate (days)", 7, 30, 7)

    # management type
    mana = st.sidebar.radio("Choose rice management", ['Conventional', 'AWD'])

    # year selection
    year_slider = st.sidebar.empty()

    # prepare data/ apply options
    ds = ds_cf[vars] if mana == 'Conventional' else ds_awd[vars]

    # for later statistics
    data_orig_cf = ds_cf_gc[gwp_vars].to_dataframe()
    data_orig_awd = ds_awd_gc[gwp_vars].to_dataframe()

    if sel_timestep == 'daily':
        data = ds.to_dataframe()
    else:
        data = ds.groupby('time.year').sum().to_dataframe()
        data.index = pd.to_datetime(data.index, format='%Y')

        # disable smooth option as we only allow it for daily data
        sel_smooth.checkbox("Smooth (daily) data", value=False, key='b')
        smooth_slider.empty()

    if smooth:
        data = data.rolling(window=smooth_rate, center=True).mean()

    min_year = data.index.min().to_pydatetime().year
    max_year = data.index.max().to_pydatetime().year

    year_filter = year_slider.slider('Select years', min_year, max_year, (min_year, max_year))

    def limit_data_df(df):
        return df[ (df.index >= str(year_filter[0])) & (df.index <= str(year_filter[1])) ] 


    data = limit_data_df(data)
    data_orig_cf = limit_data_df(data_orig_cf)
    data_orig_awd = limit_data_df(data_orig_awd)

    if only_ghg_vars:
        if 'dN_n2o_emis' in data.columns.values:
            data['dN_n2o_emis'] = convert_n2o_gwp(data['dN_n2o_emis'])
        if 'dC_ch4_emis' in data.columns.values:
            data['dC_ch4_emis'] = convert_ch4_gwp(data['dC_ch4_emis'])
    

    # plotting canvas

    # compose units for plot
    if only_ghg_vars:
        units = 'kg GWP-eq'
    elif ('dC_ch4_emis' in vars) and len(vars) == 1:
        units = 'kg C'
    else:
        units = 'kg N'

    # plots
    if sel_timestep == 'daily':
        line_plot(data, units=f'[{units} ha⁻¹ yr⁻¹]')
    else:
        bar_plot(data, units=f'[{units} yr⁻¹]')


    if show_report:
        # reporting
        st.header("Data report")

        create_report(data_orig_cf, data_orig_awd)

        # maps
        st.subheader("Spatial distribution of GHG emissions")
        st.markdown("The following maps show the average annual emission for the selected management option...")
        st.warning("⚠️ TODO: Fix performance problems in Cartopy plotting setup")
        st.pyplot(plot_maps(management=mana, year=range(year_filter[0], year_filter[1]+1)), bbox_inches='tight')

    # footer
    st.markdown("[1] GWP calculation based on the IPCC, 5th Assessment Report")


if __name__ == "__main__":
    main()