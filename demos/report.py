import streamlit as st
from utils import gwp_vars, convert_ch4_gwp, convert_n2o_gwp

def create_report(data_orig_cf, data_orig_awd):
    stats = {}
    for var in gwp_vars:
        vname = 'n2o' if 'n2o' in var else 'ch4'
        stats[vname] = {}
        for m in ['cf', 'awd']:
            stats[vname][m] = {}
            data_orig = data_orig_cf if m == 'cf' else data_orig_awd 
            annual_sum = data_orig[var].groupby(data_orig.index.year).sum(dim='index').mean()
            annual_gwp = convert_ch4_gwp(annual_sum) if vname=='ch4' else convert_n2o_gwp(annual_sum)
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


