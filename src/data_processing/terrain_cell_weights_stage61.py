"""Approved native-cell exact length weights and strict Horn terrain gradient.

EPSG2056 north-up raster: native floor row/column convention for boundary
ownership, no proximity grid, rounding, snapping, missing-value interpolation
or implicit change to source coordinates. No station acceptance or exclusions.
"""
from collections import defaultdict
import math
import numpy as np


def horn(window, x_resolution=2.0, y_resolution=2.0):
    """Slope degrees / downslope azimuth (N0,E90,S180,W270), or missing.

Every neighbour must be finite and observed. Flat centre remains a valid
altitude observation but has no defined terrain direction. Caller supplies
masked source nodata as NaN, without interpolation.
"""
    z=np.asarray(window,dtype=float)
    if z.shape!=(3,3) or x_resolution<=0 or y_resolution<=0:
        raise ValueError('Require a 3x3 window and positive native resolutions')
    if not np.isfinite(z).all():return None,None
    dx=((z[0,2]+2*z[1,2]+z[2,2])-(z[0,0]+2*z[1,0]+z[2,0]))/(8*x_resolution)
    dy=((z[0,0]+2*z[0,1]+z[0,2])-(z[2,0]+2*z[2,1]+z[2,2]))/(8*y_resolution)
    slope=math.degrees(math.atan(math.hypot(dx,dy)))
    aspect=math.degrees(math.atan2(-dx,-dy))%360 if dx!=0 or dy!=0 else None
    return slope,aspect


def cell_lengths(geometry,left,top,x_resolution=2.0,y_resolution=2.0):
    """Exact straight-piece lengths in native cells; outside cells retained.

Split each source segment at each crossed vertical/horizontal raster boundary,
then assign midpoint using native floor row/column indexing. Boundary segments
are owned by one cell, never counted twice. Returns (row,col)->length; neither
an arbitrary sample interval nor a tolerance is used.
    """
    if x_resolution<=0 or y_resolution<=0:
        raise ValueError('Require positive native cell size')
    if geometry.geom_type=='LineString':parts=[geometry]
    elif geometry.geom_type=='MultiLineString':parts=list(geometry.geoms)
    else:raise ValueError('Require unique linear network, not polygon perimeter')
    weights=defaultdict(list)
    for part in parts:
        coords=list(part.coords)
        for (x0,y0),(x1,y1) in zip(coords,coords[1:]):
            length=math.hypot(x1-x0,y1-y0)
            if not math.isfinite(length):raise ValueError('Nonfinite source coordinates')
            if length==0:continue
            c0,c1=(x0-left)/x_resolution,(x1-left)/x_resolution
            r0,r1=(top-y0)/y_resolution,(top-y1)/y_resolution
            cuts={0.0,1.0}
            for a,b in [(c0,c1),(r0,r1)]:
                if a==b:continue
                for boundary in range(math.floor(min(a,b))+1,math.ceil(max(a,b))):
                    t=(boundary-a)/(b-a)
                    if 0<t<1:cuts.add(t)
            ordered=sorted(cuts)
            for a,b in zip(ordered,ordered[1:]):
                midpoint=(a+b)/2
                col=math.floor(c0+midpoint*(c1-c0))
                row=math.floor(r0+midpoint*(r1-r0))
                weights[(row,col)].append(length*(b-a))
    result={k:math.fsum(v) for k,v in weights.items()}
    if not math.isclose(math.fsum(result.values()),geometry.length,rel_tol=1e-12,abs_tol=1e-8):
        raise ValueError('Native cell allocation must preserve exact network length')
    return result
