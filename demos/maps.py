import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import streamlit as st
import xarray as xr

from utils import convert_ch4_gwp, convert_n2o_gwp


matplotlib.rcParams.update({'font.size': 10})

# Create a feature for States/Admin 1 regions at 1:50m from Natural Earth
countries = cfeature.NaturalEarthFeature(
    category='cultural',
    name='admin_0_countries',
    scale='50m',
    facecolor='none')
    
ocean = cfeature.NaturalEarthFeature(
        category='physical', 
        name='ocean', 
        scale='50m',
        edgecolor='face',
        facecolor=cfeature.COLORS['water'])

@st.cache(allow_output_mutation=True)
def load_raw_data_awd_annual():
    return xr.open_dataset('../data/demo1_philippines/default_cf_hr_200_nobund_annual.nc')[['dC_ch4_emis', 'dN_n2o_emis']]

@st.cache(allow_output_mutation=True)
def load_raw_data_cf_annual():
    return xr.open_dataset('../data/demo1_philippines/default_cf_hr_200_nobund_annual.nc')[['dC_ch4_emis', 'dN_n2o_emis']]

def plot_maps(management='Conventional', year=None):

    Dname = {}
    Dname['dC_ch4_emis'] = r'$\mathregular{CH_4\ emission\ [kg\ C\ ha^{-1}\ yr^{-1}]}$'
    Dname['dN_n2o_emis'] = r'$\mathregular{N_2O\ emission\ [kg\ N\ ha^{-1}\ yr^{-1}]}$'
    Dname['GWP']         = r'$\mathregular{GWP\ [Mg\ CO_2\ eq\ ha^{-1}\ yr^{-1}]}$'

    if year:
        davg_cf = load_raw_data_cf_annual().sel(year=year).mean(dim='year')
        davg_awd = load_raw_data_cf_annual().sel(year=year).mean(dim='year')
    else:
        davg_cf = load_raw_data_cf_annual().mean(dim='year')
        davg_awd = load_raw_data_cf_annual().mean(dim='year')

    davg = davg_cf if management == 'Conventional' else davg_awd

    da_ch4   = davg['dC_ch4_emis']
    da_n2o   = davg['dN_n2o_emis']
    da_gwp   = convert_ch4_gwp(da_ch4) + convert_n2o_gwp(da_n2o)

    fig, axes = plt.subplots(2, 2, figsize=(10,10), subplot_kw=dict(projection=ccrs.PlateCarree()))

    for i, ax in enumerate(axes.flat):
        if i == 3:
            break
        ax.set_extent([116, 127, 4, 22])
            
        # add map elements
        ax.add_feature(countries, edgecolor='gray')     # country borders
        #ax.add_geometries(vietnam, ccrs.PlateCarree(), edgecolor='white', facecolor='none')
        ax.add_feature(ocean)                           # ocean
        ax.coastlines(resolution='50m')                 # coastlines

        if i == 0:
            colors = plt.cm.Reds
            p=xr.plot.pcolormesh(da_ch4.where(da_ch4>0), cbar_kwargs={'label': Dname['dC_ch4_emis']}, 
                        ax=ax, cmap=colors, transform=ccrs.PlateCarree(), 
                        vmin=0, vmax=1500, extend='max' )

        elif i == 1:
            colors = plt.cm.YlGn
            xr.plot.pcolormesh(da_n2o.where(da_n2o>0), cbar_kwargs={'label': Dname['dN_n2o_emis']},
                        ax=ax, cmap=colors, transform=ccrs.PlateCarree(), 
                        vmin=0, vmax=5, extend='max' )

        elif i == 2:
            colors = plt.cm.Blues
            xr.plot.pcolormesh(da_gwp.where(da_gwp>0), cbar_kwargs={'label': Dname['GWP']}, 
                        ax=ax, cmap=colors, transform=ccrs.PlateCarree(), 
                        vmin=0, vmax=50, extend='max')

        ax.add_patch(mpatches.Rectangle(xy=[116.25, 19], width=1, height=1,
                                            facecolor='none',
                                            edgecolor='black',
                                            alpha=1.0,
                                            transform=ccrs.PlateCarree()))

        sublabels = ['CH4', 'N2O', 'CH4+N2O']

        ax.text(116.5, 20.45, sublabels[i], fontsize=15,
                horizontalalignment='left', verticalalignment='center',
                transform=ccrs.PlateCarree())

    fig.delaxes(axes[1][1])

    return fig
