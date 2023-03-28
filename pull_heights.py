# -*- coding: utf-8 -*-
"""
    tephra2utils.pull_heights
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Overly elaborate docstring for a dumb single-use script.

    :copyright: (c) 2023 by YOUR_NAME.
    :license: LICENSE_NAME, see LICENSE for more details.
"""

import pandas as pd


df = pd.read_csv("wind_data.csv")

heights = df[["level", "height"]].groupby(['level']).mean()

print(heights['height'].head())

heights['height'].to_csv("heights.csv", index=False, header=None)




