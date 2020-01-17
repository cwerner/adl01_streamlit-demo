import pydeck as pdk
import streamlit as st
import numpy as np
import xarray as xr
import altair as alt
from enum import IntEnum

INTRO = """\
    ---  
    The simulations were conducted as part of [Introducing non-flooded crops in rice-dominated
    landscapes: Impact on CarbOn, Nitrogen and water budgets (ICON)](http://www.uni-giessen.de/faculties/f08/departments/tsz/animal-ecology/iconproject/iconindex)
    project.  

    Project summary:   
    > *The interdisciplinary and transdisciplinary research unit ICON aims at exploring*
    > *and quantifying the ecological consequences of future changes in rice production*
    > *in SE Asia. A particular focus lies on the consequences of altered flooding*
    > *regimes (flooded vs. non-flooded), crop diversification (wet rice vs. *
    > *dry rice vs. maize) and different crop management strategies (N fertilization)*
    > *on the biogeochemical cycling of carbon and nitrogen, the associated greenhouse gas*
    > *emissions, the water balance, and other important ecosystem services of rice*
    > *cropping systems.*
    
    ---  
    """

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

color = dotdict(green = '#bda346',
                brown = '#77ae79',
                gray = '#f0f2f6')

class GWP(IntEnum):
    N2O = 298
    CH4 = 34

def convert_ch4_gwp(value):
    return value * (16./12.) * GWP.CH4

def convert_n2o_gwp(value):
    return value * (44./28.) * GWP.N2O 

# dicts for nicer naming
mana_names = {'CF': 'Continuously Flooded (CF)', 
              'AWD': 'Alternate Wet-Dry (AWD)'}

names = {'ch4_gwp': 'CH4 Emission', 
         'n2o_gwp': 'N2O Emission', 
         'total_gwp': 'Total Emission'}


def scale(x, xmin, xmax):
    return (x - xmin)/(xmax-xmin)


def compute_rgb(data, var):
    """a wacky way to compute three different color ranges"""
    bcol = {'ch4_gwp': 20, 'n2o_gwp': 60}.get(var, 100)
    return [[(255-bcol*2), 150 + 100*(1-d), bcol*2.5] for d in data]

def generate_json(ds, var='ch4_gwp', bounds=None):
    v = ds[var] #.mean(dim='year')
        
    df = v.to_dataframe().reset_index()
    df = df[df[var] > 0]
    x = df[var]
    values = scale(x, *bounds) if bounds else x
    locs = list(zip(df.lon, df.lat))
    colors = compute_rgb(values, var)
    return [{'h': 60*h, 'pos': list(p), 'c': c} for h,p,c in zip(values,locs,colors)]


def process_df(df, vars):
    df_ = df.reset_index()[vars] if vars else df.reset_index()
    if vars is None:
        vars = list(df.columns.values)

    # rename columns
    nice_names = {'n2o_gwp': 'N₂O', 'ch4_gwp': 'CH₄'}
    for v in vars:
        df_ = df_.rename({v: nice_names.get(v)}, axis=1)

    df_ = df_.melt('year', var_name='variable', value_name='value')
    return (df_.year, df_)

def bar_plot(ds, vars=None):
    
    df = ds.to_dataframe() * 1e-6
    index_, df_ = process_df(df, vars)
    units_ = 'Gg CO₂-eq yr⁻¹'
    
    c = alt.Chart(df_).mark_bar().encode(
            alt.X('year:O', title=''),
            alt.Y('value:Q', title=f'{units_}', 
                   scale=alt.Scale(domain=[0, 120_000])), 
            alt.Color('variable:N', 
                      scale=alt.Scale(range=[color.green, color.brown]),
                      legend=alt.Legend(title='')),
            order=alt.Order('value', sort='descending')
        ).configure_axis(
            grid=False
        ).properties(
            height=200, 
            background=color.gray
        )
    st.sidebar.altair_chart(c, use_container_width=True)  


@st.cache(allow_output_mutation=True)
def load_data_awd():
    return xr.open_dataset('./data/default_awd_hr_200_nobund_annual.nc')

@st.cache(allow_output_mutation=True)
def load_data_cf():
    return xr.open_dataset('./data/default_cf_hr_200_nobund_annual.nc')

@st.cache(allow_output_mutation=True)
def load_data_area():
    return xr.open_dataset('./data/PH_MISC2.nc')


def main():
    st.title("Greenhouse gas emissions from rice paddies of the Philippines")
    st.markdown("""\
        [LandscapeDNDC](https://ldndc.imk-ifu.kit.edu) simulations conducted
        as part of the [ICON [1]](http://www.uni-giessen.de/faculties/f08/departments/tsz/animal-ecology/iconproject/iconindex)
        project by [David Kraus](https://www.imk-ifu.kit.edu/staff_David_Kraus.php)
        and [Christian Werner](https://www.imk-ifu.kit.edu/staff_Christian_Werner.php) 
        :two_men_holding_hands:, [IMK-IFU/ KIT Campus Alpin](https://www.imk-ifu.kit.edu), 
        Karlsruhe Institue of Technology.  
        """)

    intro = st.checkbox("[1] show some background information", value=False)
    if intro:
        st.write(INTRO)

    st.sidebar.subheader("Data selection")

    mana = st.sidebar.radio("Management", ["CF", "AWD"], 0, format_func=mana_names.get)

    # get netcdf data 
    ds_cf = load_data_cf()
    ds_awd = load_data_awd()
    ds = ds_cf if mana.lower() == 'cf' else ds_awd

   
    ds_area = load_data_area()
    area = ds_area.area_ha * (ds_area.ricearea * 0.01)

    ds['n2o_gwp'] = convert_n2o_gwp( ds.dN_n2o_emis )
    ds['ch4_gwp'] = convert_ch4_gwp( ds.dC_ch4_emis )
    ds['total_gwp'] = ds.ch4_gwp + ds.n2o_gwp

    # get min/ max values
    min_val, max_val = ds.total_gwp.min().values, ds.total_gwp.max().values

    # calculate total emissions (scaled by area)
    ds_sum = (ds[['ch4_gwp','n2o_gwp']] * area).sum(dim=["lat", "lon"])

    year = st.slider("Select simulation year", 2000, 2012, 2006)
    ghg = st.sidebar.radio("Emission", ["n2o_gwp", "ch4_gwp", "total_gwp"], 2, format_func=names.get)


    layer = pdk.Layer(
        'GridCellLayer',
        generate_json(ds.sel(year=year) , var=ghg, bounds=(min_val, max_val)),
        get_position='pos',
        extruded= True, 
        get_fill_color='c',
        get_elevation = 'h',
        cell_size=10000,
        elevation_scale= 1000,
        coverage=.85
    )

    view_state = pdk.ViewState(latitude=11, longitude=122, zoom=5, pitch=33)

    r = pdk.Deck(layers=[layer], initial_view_state=view_state, map_style='')
    st.write(r)

    def compute_stats(ds, how='annual'):
        # stats - selected year
        ds_ = ds.sel(year=year) if how == 'annual' else ds_sum.mean(dim='year')
        n2o = ds_.n2o_gwp.values * 1e-6
        ch4 = ds_.ch4_gwp.values * 1e-6
        tot = n2o + ch4        
        return (tot, n2o, ch4)

    # stats - selected year and average
    tot_sel, n2o_sel, ch4_sel = compute_stats(ds_sum, how="annual")
    tot_avg, n2o_avg, ch4_avg = compute_stats(ds_sum, how="average")

    st.sidebar.subheader("Summary stats")

    bar_plot(ds_sum)

    st.sidebar.info(f"""\
        ### Total emissions ({mana})  

        |     |   {year}        |  avg             |   
        |-----|----------------:|-----------------:|  
        |CH₄  |`{ch4_sel:,.0f}` | `{ch4_avg:,.0f}` |
        |N₂O  |`{n2o_sel:,.0f}` | `{n2o_avg:,.0f}` |
        |sum  |`{tot_sel:,.0f}` | `{tot_avg:,.0f}` |

        units: Gg CO₂-eq yr⁻¹      
        """)


if __name__ == "__main__":
    main()
