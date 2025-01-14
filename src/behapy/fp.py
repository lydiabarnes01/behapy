from typing import Tuple, Iterable
import numpy as np
import scipy.signal as sig
from collections import namedtuple
from typing import Iterable


Event = namedtuple('Event', ['name', 'fields', 'codes', 'onset', 'offset'])


def map_events(events: Iterable[Event]):
    """ Create a dict mapping event codes to the respective events. """
    return {key: event for event in events.values() for key in event.fields}


def invalidate_samples(df, start, end):
    """Invalidate samples """
    if start == None:
        start = df.index[0]
    if end == None:
        end = df.index[-1]
    if 'Valid' not in df:
        df['Valid'] = True
    df.loc[start:end, 'Valid'] = False
    return df


def smooth(x, fs):
    try:
        b = smooth.filter_b
    except AttributeError:
        b = sig.firwin2(int(fs*8), freq=[0, 0.01, 0.05, fs/2],
                        gain=[1.0, 1.0, 0.0001, 0.0], fs=fs)
        smooth.filter_b = b
    xds = sig.decimate(x, 10, ftype='fir', zero_phase=True)
    xf = sig.filtfilt(b, 1, xds)
    return sig.resample(xf, x.shape[0])


def detrend_hp(x, fs):
    try:
        b = detrend_hp.filter_b
    except AttributeError:
        # b = sig.firwin2(int(fs*8), freq=[0, 0.1, 0.2, 0.4, fs/2],
        #                 gain=[0., 1e-7, 0.1, 1., 1.], fs=fs)
        b = sig.firwin2(1001, freq=[0, 0.05, 0.1, fs/2],
                        gain=[0., 0.001, 1., 1.], fs=fs)
        detrend_hp.filter_b = b
    return sig.filtfilt(b, 1, x)

    
def normalise(signal, control, mask, fs, method='fit', detrend=True):
    # smoothed = smooth(control[~mask], fs=fs)
    smoothed = control[~mask]
    fit = np.polyfit(smoothed, signal[~mask], deg=1)
    # Subtract the smoothed projection - fitting the raw control
    # projection results in a greater variance in the fitted signal than
    # the actual signal
    signal_fit = signal.copy()
    signal_fit[~mask] = fit[0] * smoothed + fit[1]
    df = signal - signal_fit
    if detrend:
        # Filter with a highpass filter to remove remaining drift
        df = detrend_hp(df, fs)
        
    if method == 'fit':
        dff = df / signal_fit
        return dff / dff.std()
    elif method == 'const':
        dff = df / np.mean(signal)
        return dff / dff.std()
    elif method == 'df':
        return df
    elif method == 'yfit':
        return signal_fit
    else:
        raise ValueError("Unrecognised normalisation method {}".format(method))


def collect_tdt_events(raw, events):
    ts = np.array([])
    keys = np.array([])
    event_map = map_events(events)
    for key in raw.epocs.keys() & event_map.keys():
        ts = np.append(ts, raw.epocs[key].onset)
        keys = np.append(keys, [key] * len(raw.epocs[key].onset))
    order = np.argsort(ts)
    return ts[order], keys[order]


def epoch_events(data: Iterable[float],
                 events: Iterable[float],
                 window: Tuple[float, float],
                 baseline_window: Tuple[float, float],
                 fs: float, tstart: float = 0.,
                 method: str = 'z') -> Tuple[np.ndarray, np.ndarray]:
    """ Epoch data at supplied event times and optionally baseline.

    Args:
        data: An array of samples.
        events: An array containing event times in seconds (must be sorted).
        window: Start and end time of epoch in seconds, e.g. (-1.0, 1.0).
        baseline_window: Start and end time of baseline period for each
            epoch in seconds, if required, e.g. (-2.0, -1.0).
        fs: Sampling frequency of data,
        tstart: Time in seconds of the first sample of data,
        method: Baselining method, either z-scored ('z', default),
            baseline mean subtracted ('base') or unbaselined signal ('nobase').
    
    Returns:
        Array of (baselined) epoch values with a correponding timestamp array.
    """
    n = data.shape[0]
    ts = np.arange(n) / fs + tstart
    ixs = np.searchsorted(ts, events)
    window_ix = np.ceil(np.array(window) * fs).astype(int)
    if method != 'nobase':
        baseline_ix = np.ceil(np.array(baseline_window) * fs).astype(int)
    dslice = lambda b, w: data[slice(*(b + w))]
    if method == 'z':
        z = lambda d, b: (d - np.mean(b)) / np.std(b)
        epochs = np.array([z(dslice(ix, window_ix), dslice(ix, baseline_ix))
                           for ix in ixs])
    elif method == 'base':
        base = lambda d, b: d - np.mean(b)
        epochs = np.array([base(dslice(ix, window_ix), dslice(ix, baseline_ix))
                           for ix in ixs])
    elif method == 'nobase':
        epochs = np.array([dslice(ix, window_ix)
                           for ix in ixs])
    else:
        raise ValueError('Invalid epoching method {}'.format(method))

    return epochs, np.arange(*window_ix) / fs
