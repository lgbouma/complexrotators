"""
Contents:
    plot_river
"""
import os, corner, pickle
from glob import glob
from datetime import datetime
import numpy as np, matplotlib.pyplot as plt, pandas as pd, pymc3 as pm
from numpy import array as nparr

import matplotlib as mpl

from astropy import units as u, constants as const
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.time import Time
from astropy.table import Table

import matplotlib.patheffects as pe
from matplotlib.ticker import MaxNLocator

from aesthetic.plot import savefig, format_ax, set_style

def plot_river(time, flux, period, outdir, titlestr=None, cmap='Blues_r',
               cyclewindow=None):
    """
    Make a river plot
    """

    t0 = np.nanmin(time)
    flux -= np.nanmedian(flux) # already normalized

    cadence = np.nanmedian(np.diff(time)) # 2 minutes, in units of days
    N_obs_per_cycle = int(period / cadence)

    cycle_number = np.floor( (time-t0) / period)

    cycle_min = int(np.min(cycle_number))
    cycle_max = int(np.max(cycle_number))

    flux_arr = np.zeros(
        (N_obs_per_cycle, cycle_max-cycle_min)
    )

    for cycle_ind in range(cycle_min, cycle_max):

        begin = t0 + period*cycle_ind
        end = t0 + period*(cycle_ind+1)

        sel = (time > begin) & (time <= end)

        if len(flux[sel]) < (N_obs_per_cycle-5):
            # for significantly empty cycles, do all nan.  "significantly
            # empty" here means any more than 5 cadences (10 minutes, out of a
            # ~1 day periods typically) off.
            flux_arr[:, cycle_ind] = 0

        elif len(flux[sel]) < N_obs_per_cycle:
            # for cycles a few cadences short, pad with a few nans at the end
            # of the array
            use_flux = np.ones(N_obs_per_cycle)*0

            # the beginning of the array is the flux
            use_flux[:flux[sel].shape[0]] = flux[sel]

            flux_arr[:, cycle_ind] = use_flux

        elif len(flux[sel]) < (N_obs_per_cycle+5):
            use_flux = flux[sel][:N_obs_per_cycle]
            flux_arr[:, cycle_ind] = use_flux

        elif len(flux[sel]) > (N_obs_per_cycle+5):
            raise NotImplementedError('How did this happen?')

        else:
            use_flux = flux[sel]
            flux_arr[:, cycle_ind] = use_flux

    vmin = np.nanmedian(flux)-5*np.nanstd(flux)
    vmax = np.nanmedian(flux)+5*np.nanstd(flux)

    fig, ax = plt.subplots(figsize=(4,10))
    c = ax.pcolor(np.arange(0, period, cadence),
                  list(range(cycle_min, cycle_max)),
                  flux_arr.T,
                  cmap=cmap, vmin=vmin, vmax=vmax)

    fig.colorbar(c, ax=ax)

    if isinstance(titlestr, str):
        ax.set_title(titlestr)
    ax.set_ylabel('Cycle number')
    ax.set_xlabel('Time [days]')

    if isinstance(cyclewindow, tuple):
        ax.set_ylim(cyclewindow)

    if isinstance(titlestr, str):
        estr = ''
        if isinstance(cyclewindow, tuple):
            estr += (
                "_"+repr(cyclewindow).
                replace(', ','_').replace('(','').replace(')','')
            )
        outpath = os.path.join(outdir, f'{titlestr}_river_{cmap}{estr}.png')
    else:
        raise NotImplementedError

    savefig(fig, outpath, writepdf=0)