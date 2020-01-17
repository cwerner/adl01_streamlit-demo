INTRO = """\
        ## Introduction
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
        > *cropping systems.*"""


# GWP for 100-yr time horizon  according to 5th IPCC report
n2o_gwp = 298
ch4_gwp = 38

gwp_vars = ['dN_n2o_emis', 'dC_ch4_emis']

def convert_ch4_gwp(value):
    return value * ch4_gwp * (16./12.)

def convert_n2o_gwp(value):
    return value * n2o_gwp * (44./28.)

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


