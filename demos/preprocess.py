import xarray as xr

PATH='../data/demo1_philippines'
for m in ['cf', 'awd']:
    FILE1=f'default_{m}_hr_200_nobund_daily.nc'
    FILE2A=f'default_{m}_hr_200_nobund_daily_ts_ha.nc'
    FILE2B=f'default_{m}_hr_200_nobund_daily_ts_gridcell.nc'
    FILE2C=f'default_{m}_hr_200_nobund_annual.nc'

    AREA='PH_MISC2.nc'
    dsa = xr.open_dataset(f"{PATH}/{AREA}")
    area = dsa['area_ha'] * (dsa['ricearea'] * 0.01)

    ds0 = xr.open_dataset(f"{PATH}/{FILE1}").groupby('time.year').sum(dim='time')
    ds0.to_netcdf(f"{PATH}/{FILE2C}")

    #ds1 = xr.open_dataset(f"{PATH}/{FILE1}").mean(dim=['lat','lon'])
    #ds1.to_netcdf(f"{PATH}/{FILE2A}")

    #ds2 = (xr.open_dataset(f"{PATH}/{FILE1}") * area).mean(dim=['lat','lon'])
    #ds2.to_netcdf(f"{PATH}/{FILE2B}")


