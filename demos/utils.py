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


# import pandas as pd
# import pint

# u = pint.UnitRegistry()

# class Data:
#     def __init__(self, x):
#         self.flux = x*u.kg/u.hectare

#     def __repr__(self):
#         return f"{self.flux}"

# if __name__ == '__main__':
#     d = Data(12)
#     print(d)

#     import pandas as pd
#     import pint
#     import io

#     test_data = '''speed,mech power,torque,rail pressure,fuel flow rate,fluid power
# rpm,kW,N m,bar,l/min,kW
# 1000.0,,10.0,1000.0,10.0,
# 1100.0,,10.0,100000000.0,10.0,
# 1200.0,,10.0,1000.0,10.0,
# 1200.0,,10.0,1000.0,10.0,'''

#     df = pd.read_csv(io.StringIO(test_data),header=[0,1])
#     print(df)

#     print(df.dtypes)

#     df_ = df.pint.quantify(level=-1)
#     print(df_)
