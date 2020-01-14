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

st.header('Data explorer for LandscapeDNDC Philippines sims')

descr = st.checkbox("Show description", value=True)

if descr:
    st.markdown("""\
        We use [streamlit](https://streamlit.io) to explore some simulation 
        results of the [LandscapeDNDC](https://ldndc.imk-ifu.kit.edu) biogeochemical model. The 
        simulations were conducted as part of [Introducing non-flooded crops in rice-dominated
        landscapes: Impact on CarbOn, Nitrogen and water budgets (ICON)](http://www.uni-giessen.de/faculties/f08/departments/tsz/animal-ecology/iconproject/iconindex)
        by [David Kraus](https://www.imk-ifu.kit.edu/staff_David_Kraus.php) and 
        [Christian Werner](https://www.imk-ifu.kit.edu/staff_Christian_Werner.php) at Campus Alpin, IMK-IFU,
        Karlsruhe Institute of Technology.

        A brief summary of the project:   
        > *The interdisciplinary and transdisciplinary research unit ICON aims at exploring*
        > *and quantify- ing the ecological consequences of future changes in rice production*
        > *in SE Asia. A particular focus will be on the consequences of altered flooding*
        > *regimes (flooded vs. non-flooded), crop diversification (wet rice vs. *
        > *dry rice vs. maize) and different crop management strategies (N fertilization)*
        > *on the biogeochemical cycling of carbon and nitrogen, the associated greenhouse gas*
        > *emissions, the water balance, and other important ecosystem services of rice*
        > *cropping systems.*""")

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

# @st.cache(show_spinner=False)
# def load_nongendered_data():
#     df = pd.read_csv("data/total.csv", index_col=0)
#     return df

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

st.subheader("Data exploration")
only_ghg_vars = st.checkbox('Only GHG emissions (values converted to GWP [1])')
if only_ghg_vars:
    fluxes = ['dN_n2o_emis', 'dC_ch4_emis']

vars = st.multiselect("Select one or multiple variables to plot", 
                      fluxes, 
                      default=['dN_n2o_emis'],
                      format_func=fluxnames.get)

# if no variable is selected pick the first one so the script does not crash
if len(vars) == 0:
    vars = fluxes[0]

# sidebar options
st.sidebar.subheader("Time range/ resolution")
ts = st.sidebar.radio("Show daily or annual data", ['daily', 'annual'])

smooth_chk = st.sidebar.empty()
smooth_slider = st.sidebar.empty()

smooth = smooth_chk.checkbox("Smooth (daily) data", key='0')

if smooth:
    smooth_rate = smooth_slider.slider("Smooth rate (days)", 7, 30, 7)

year_slider = st.sidebar.empty()

st.sidebar.subheader("Management")
mana = st.sidebar.radio("Choose management type", ['conventional', 'AWD'])

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

year_filter = year_slider.slider('Year range', min_year, max_year, (min_year, max_year))
#data = data[ (data.index >= str(year_filter[0])) & (data.index <= str(year_filter[1])) ]

def limit_data(df):
    return df[ (df.index >= str(year_filter[0])) & (df.index <= str(year_filter[1])) ] 

data = limit_data(data)
data_orig_cf = limit_data(data_orig_cf)
data_orig_awd = limit_data(data_orig_awd)

if only_ghg_vars:
    if 'dN_n2o_emis' in data.columns.values:
        data['dN_n2o_emis'] = data['dN_n2o_emis'] * n2o_gwp
    if 'dC_ch4_emis' in data.columns.values:
        data['dC_ch4_emis'] = data['dC_ch4_emis'] * ch4_gwp
    

st.sidebar.subheader("Other options")

show_data = st.sidebar.checkbox("Show data", value=False)
show_code = st.sidebar.checkbox("Show code", value=False)


# MAIN CANVAS


def line_plot(df, vars=None, kind='line', index=None):
    """A more explicit plotting routine"""
    df_ = df.reset_index()[vars] if vars else df.reset_index()
    if vars is None:
        vars = list(df.columns.values)

    # rename columns
    for v in vars:
        df_ = df_.rename({v: fluxnames.get(v)}, axis=1)

    df_ = df_.melt('time', var_name='variable', value_name='value')
    c = alt.Chart(df_).mark_line().encode(
            alt.X('time:T', title=''),
            alt.Y('value:Q', title='Flux [kg N yr-1]'), # axis=alt.Axis(title="Flux [kg N yr-1]")),
            alt.Color('variable:N', legend=alt.Legend(title='')), #, mapping=fluxnames)),
        ).configure_axis(
            grid=False
        )
    st.altair_chart(c)


# plots
if ts == 'daily':
    #    st.line_chart(data)
    line_plot(data)

else:
    st.bar_chart(data)



# reporting
st.subheader("Summary report")

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
    `{stats['n2o'][m]['annual']:.2f} kg N yr-1` (or `{(stats['n2o'][m]['daily']*1000):.1f} kg N d-1`), 
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


# extra
if show_data:
    st.subheader("The current data selection")
    st.write(data)

if show_code:
    st.subheader("The code of this demo")
    st.code(open(__file__).read())

