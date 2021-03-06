"""Routines to download Earth orientation data."""

import numpy as np
import os
from skyfield.iokit import load
from skyfield.timelib import julian_date

def morrison_and_stephenson_2004_table():
    """Table of smoothed Delta T values from Morrison and Stephenson, 2004."""
    import pandas as pd
    f = load('http://eclipse.gsfc.nasa.gov/SEcat5/deltat.html')
    tables = pd.read_html(f.read())
    df = tables[0]
    return pd.DataFrame({'year': df[0], 'delta_t': df[1]})

def usno_historic_delta_t():
    import pandas as pd
    f = load('http://maia.usno.navy.mil/ser7/historic_deltat.data')
    df = pd.read_table(f, sep=r' +', engine='python', skiprows=[1])
    return pd.DataFrame({'year': df['Year'], 'delta_t': df['TDT-UT1']})

def main():
    thisdir = os.path.dirname(__file__)

    df = morrison_and_stephenson_2004_table()
    year = df.year.values
    jd = julian_date(year, 1, 1)
    delta_t = df.delta_t.values
    array = np.array((jd, delta_t))
    np.save(os.path.join(thisdir, 'morrison_stephenson_deltat.npy'),
            array)

    df = usno_historic_delta_t()
    year = df.year.values
    jd = julian_date(year, 1, 1)
    delta_t = df.delta_t.values
    array = np.array((jd, delta_t))
    np.save(os.path.join(thisdir, 'historic_deltat.npy'),
            array)

if __name__ == '__main__':
    main()
