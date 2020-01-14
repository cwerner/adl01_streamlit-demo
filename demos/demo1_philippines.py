import streamlit as st
import numpy as np
import pandas as pd
#from utils import hdi
from string import capwords
import textwrap
import xarray as xr
import datetime
import altair as alt

# GWP for 100-yr time horizon  according to 5th IPCC report
n2o_gwp = 265
ch4_gwp = 28

def convert_ch4_gwp(value):
    return value * ch4_gwp * (16./12.)

def convert_n2o_gwp(value):
    return value * n2o_gwp * (44./28.)

def identify_index_col(df):
    for c in df.columns.values:
        print(c)
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

def line_plot(df, vars=None):

    index_, df_ = process_df(df, vars)
    c = alt.Chart(df_).mark_line().encode(
            alt.X(f'{index_}:T', title=''),
            alt.Y('value:Q', title='Flux [kg N yr-1]'), 
            alt.Color('variable:N', legend=alt.Legend(title='')), 
        ).configure_axis(
            grid=False
        )
    st.altair_chart(c)

def bar_plot(df, vars=None):

    index_, df_ = process_df(df, vars)
    df_['year'] = df_[index_].dt.year
    c = alt.Chart(df_).mark_bar().encode(
            alt.X('year:O', title=''),
            alt.Y('value:Q', title='Flux [kg N yr-1]'), 
            alt.Color('variable:N', legend=alt.Legend(title='')), 
        ).configure_axis(
            grid=False
        )
    st.altair_chart(c)    


st.title('Data explorer for LandscapeDNDC Philippines sims')

st.sidebar.header("Options")
st.sidebar.subheader("General")

show_intro = st.sidebar.checkbox("Show intro", value=True)
show_code = st.sidebar.checkbox("Show code", value=False)

if show_intro:
    st.markdown("""\
        ## Intro
        We use [streamlit](https://streamlit.io) to explore some simulation 
        results of the [LandscapeDNDC](https://ldndc.imk-ifu.kit.edu) biogeochemical model. The 
        simulations were conducted as part of [Introducing non-flooded crops in rice-dominated
        landscapes: Impact on CarbOn, Nitrogen and water budgets (ICON)](http://www.uni-giessen.de/faculties/f08/departments/tsz/animal-ecology/iconproject/iconindex)
        by [David Kraus](https://www.imk-ifu.kit.edu/staff_David_Kraus.php) and 
        [Christian Werner](https://www.imk-ifu.kit.edu/staff_Christian_Werner.php) at Campus Alpin, IMK-IFU,
        Karlsruhe Institute of Technology.

        A brief summary of the project:   
        > *The interdisciplinary and transdisciplinary research unit ICON aims at exploring*
        > *and quantifying the ecological consequences of future changes in rice production*
        > *in SE Asia. A particular focus lies on the consequences of altered flooding*
        > *regimes (flooded vs. non-flooded), crop diversification (wet rice vs. *
        > *dry rice vs. maize) and different crop management strategies (N fertilization)*
        > *on the biogeochemical cycling of carbon and nitrogen, the associated greenhouse gas*
        > *emissions, the water balance, and other important ecosystem services of rice*
        > *cropping systems.*""")

if show_code:
    st.header("The streamlit code of this demo")
    st.markdown("Check out the full source code of this app at https://www.github.com/cwerner/adl01_streamlit-demo.")
    st.code(open(__file__).read())

st.markdown("""\
    App created by
    [Christian Werner (christian.werner@kit.edu)](https://www.christianwerner.net)\n""")

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

varsubset = []
varnames = {'aC_change': 'annual C change',
            'aN_change': 'annual N change',
            'C_soil': 'soil C stocks',
            'N_soil': 'soil N stocks'}

ds_awd = load_raw_data_awd()
ds_cf  = load_raw_data_cf()

ds_awd_gc = load_raw_data_awd_gridcell()
ds_cf_gc  = load_raw_data_cf_gridcell()

# some simple altair plot
fluxes = [v for v in ds_awd.data_vars.keys() if 'dN_' in v] + \
         [v for v in ds_awd.data_vars.keys() if 'dC_' in v]

fluxes = [f for f in fluxes if f not in ['dN_litter','dN_fertilizer','dC_bud']]
fluxnames = {'dN_n2o_emis': 'N2O Emission', 
             'dN_no_emis': 'NO(x) Emission',
             'dN_nh3_emis': 'NH3 Emission',
             'dN_n2_emis': 'N2 Emission',
             'dN_no3_leach': 'NO3 Leaching',
             'dN_nh4_leach': 'NH4 leaching',
             'dN_don_leach': 'DON leaching',
             'dN_up_min': 'Plant N uptake',
             'dN_dep': 'Atmos. N deposition',
             'dN_n2_fix': 'Biological N fixation',
             'dC_ch4_emis': 'CH4 Emission'}

vargroups = {'N gas exchange': ['dN_n2o_emis', 'dN_no_emis', 'dN_nh3_emis', 'dN_n2_emis', 'dN_dep', 'dN_n2_fix'] ,
             'N leaching': [], 
             'other': [] }

st.header("Data exploration")

only_ghg_vars = st.checkbox('Only GHG emissions (values converted to GWP [1])')
if only_ghg_vars:
    fluxes = ['dN_n2o_emis', 'dC_ch4_emis']
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
    vars = sel_vars.multiselect("Pick one or multiple variables (click into field for selection)", 
                                fluxes, 
                                default=default_sel,
                                format_func=fluxnames.get, key='b')


if (('dC_ch4_emis' in vars) and len(vars) > 1 and only_ghg_vars == False):
    st.warning("⚠️ C and N variables in same plot. Tick option above... Only N-based fluxes shown.")
    vars.remove('dC_ch4_emis')

# sidebar options
st.sidebar.subheader("Data selection")
ts = st.sidebar.radio("Show daily or annual data", ['daily', 'annual'])

smooth_chk = st.sidebar.empty()
smooth_slider = st.sidebar.empty()

smooth = smooth_chk.checkbox("Smooth (daily) data", key='0')

if smooth:
    smooth_rate = smooth_slider.slider("smoothing rate (days)", 7, 30, 7)

year_slider = st.sidebar.empty()

mana = st.sidebar.radio("Choose rice management", ['Conventional', 'AWD'])

# prepare data/ apply options
ds = ds_cf[vars] if mana == 'conventional' else ds_awd[vars]

# for later statistics
gwp_vars = ['dN_n2o_emis', 'dC_ch4_emis']
data_orig_cf = ds_cf_gc[gwp_vars].to_dataframe()
data_orig_awd = ds_awd_gc[gwp_vars].to_dataframe()

if ts == 'daily':
    data = ds.to_dataframe()
else:
    data = ds.groupby('time.year').sum().to_dataframe()
    data.index = pd.to_datetime(data.index, format='%Y')

    # disable smooth option as we only allow it for daily data
    smooth_chk.checkbox("Smooth (daily) data", value=False, key='b')
    smooth_slider.empty()

if smooth:
    data = data.rolling(window=smooth_rate, center=True).mean()

min_year = data.index.min().to_pydatetime().year
max_year = data.index.max().to_pydatetime().year

year_filter = year_slider.slider('year range', min_year, max_year, (min_year, max_year))
#data = data[ (data.index >= str(year_filter[0])) & (data.index <= str(year_filter[1])) ]

def limit_data(df):
    return df[ (df.index >= str(year_filter[0])) & (df.index <= str(year_filter[1])) ] 

data = limit_data(data)
data_orig_cf = limit_data(data_orig_cf)
data_orig_awd = limit_data(data_orig_awd)

if only_ghg_vars:
    if 'dN_n2o_emis' in data.columns.values:
        data['dN_n2o_emis'] = convert_n2o_gwp(data['dN_n2o_emis'])
    if 'dC_ch4_emis' in data.columns.values:
        data['dC_ch4_emis'] = convert_ch4_gwp(data['dC_ch4_emis'])
   


# MAIN CANVAS

# plots
if ts == 'daily':
    line_plot(data)
else:
    bar_plot(data)

# reporting
st.header("Data report")

stats = {}
for var in gwp_vars:
    gwp = n2o_gwp if 'n2o' in var else ch4_gwp
    vname = 'n2o' if 'n2o' in var else 'ch4'
    stats[vname] = {}
    for m in ['cf', 'awd']:
        stats[vname][m] = {}
        data_orig = data_orig_cf if m == 'cf' else data_orig_awd 
        annual_sum = data_orig[var].groupby(data_orig.index.year).sum().mean()
        annual_gwp = annual_sum * gwp
        daily_mean = data_orig[var].mean()
        stats[vname][m]['annual'] = annual_sum
        stats[vname][m]['gwp'] = annual_gwp
        stats[vname][m]['daily'] = daily_mean

# individual contributions (conventional)
m = 'cf'
st.markdown( f"""
    With conventional management, rice paddies of the Philippines emitted
    `{stats['ch4'][m]['annual']:.1f} kg C yr-1` (or `{stats['ch4'][m]['daily']:.2f} kg C d-1`)
    as `Methane`. This amounts to a GWP-equivalent of `{int(stats['ch4'][m]['gwp'])} CO2-eq yr-1` [1].
    In addition, `N2O emissions` of `{stats['n2o'][m]['annual']:.2f} kg N yr-1` (or
    `{(stats['n2o'][m]['daily']*1000):.1f} g N d-1`) were released to the atmosphere. 
    These emissions amount to `{int(stats['n2o'][m]['gwp'])} kg CO2-eq yr-1`.  
    """)

# individual contributions (awd)
m = 'awd'

st.markdown( f"""    
    If management would be switched to alternate-wetting and drying (AWD) technique,
    `{stats['ch4'][m]['annual']:.1f} kg C yr-1` (or `{stats['ch4'][m]['daily']:.2f} kg C d-1`),
    which is equivalent to `{int(stats['ch4'][m]['gwp'])} kg CO2-eq yr-1`, would be released `as Methane`. 
    However, this management change would also result in `N2O emissions` of 
    `{stats['n2o'][m]['annual']:.2f} kg N yr-1` (or `{(stats['n2o'][m]['daily']*1000):.1f} g N d-1`), 
    which would be equivalent to `{int(stats['n2o'][m]['gwp'])} kg CO2-eq yr-1`.
    """)

awd_deployed = st.slider("Ratio of AWD deployment", 1, 100, 50)

# comparison
cf_total = (stats['ch4']['cf']['gwp'] + stats['n2o']['cf']['gwp']) 
awd_total = (stats['ch4']['awd']['gwp'] + stats['n2o']['awd']['gwp']) * (awd_deployed * 0.01) + \
            (stats['ch4']['cf']['gwp'] + stats['n2o']['cf']['gwp']) * (1 - (awd_deployed * 0.01))

diff = abs(cf_total - awd_total)

change = 'lower' if awd_total < cf_total else 'raise'
change2 = 'reduction' if awd_total < cf_total else 'increase'

change_pct = abs(1 - (awd_total / cf_total))*100

st.markdown( f"""
    >**A `{awd_deployed}% change to AWD` management would thus `{change}` the total GHG emissions
    from rice paddies by `{change_pct:.1f} %` (a `GWP {change2} of {diff:.0f} kg CO2-eq yr-1`) compared to the conventional practice.**""")

st.markdown("[1] GWP calculation based on the IPCC, 5th Assessment Report")


