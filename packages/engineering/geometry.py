"""Versioned local geometry and exact minimum-curvature path interpolation."""
import bisect
import math
from typing import Literal
from pydantic import Field, model_validator
from .models import Contract, SurveyRequest
from .physics import minimum_curvature


class InterpretedTop(Contract):
    name: str = Field(min_length=1, max_length=80)
    top_tvd_m: float = Field(ge=0, le=30000)
    uncertainty_m: float = Field(ge=0, le=10000)
    category: Literal["formation", "aquifer", "reactive", "fault"] = "formation"
    source: str = Field(min_length=3, max_length=300)
    interpretation: Literal["interpreted", "synthetic"]


class HoleSection(Contract):
    name: str = Field(min_length=1, max_length=80)
    top_md_m: float = Field(ge=0, le=30000)
    bottom_md_m: float = Field(gt=0, le=30000)
    diameter_m: float = Field(ge=.005, le=3)
    source: str = Field(min_length=3, max_length=300)

    @model_validator(mode="after")
    def interval(self):
        if self.bottom_md_m <= self.top_md_m:
            raise ValueError("Hole-section bottom must exceed top MD.")
        return self


class CasingRecord(Contract):
    name: str = Field(min_length=1, max_length=80)
    top_md_m: float = Field(ge=0, le=30000)
    bottom_md_m: float = Field(gt=0, le=30000)
    outside_diameter_m: float = Field(ge=.005, le=2)
    inside_diameter_m: float = Field(ge=.001, le=2)
    minimum_wall_m: float = Field(ge=1e-5, le=1)
    wall_loss_allowance_m: float = Field(ge=0, le=.5)
    state: Literal["planned", "installed"]
    grade: str = Field(min_length=1, max_length=80)
    source: str = Field(min_length=3, max_length=300)
    yield_strength_pa: float | None = Field(default=None, ge=1, le=2e9)
    body_burst_pa: float | None = Field(default=None, ge=1, le=1e9)
    body_collapse_pa: float | None = Field(default=None, ge=1, le=1e9)
    body_tension_n: float | None = Field(default=None, ge=1, le=1e9)
    body_compression_n: float | None = Field(default=None, ge=1, le=1e9)
    connection_burst_pa: float | None = Field(default=None, ge=1, le=1e9)
    connection_collapse_pa: float | None = Field(default=None, ge=1, le=1e9)
    connection_tension_n: float | None = Field(default=None, ge=1, le=1e9)
    connection_compression_n: float | None = Field(default=None, ge=1, le=1e9)
    body_rating_source: str | None = Field(default=None, min_length=3, max_length=300)
    connection_rating_source: str | None = Field(default=None, min_length=3, max_length=300)
    cost_per_m: float | None = Field(default=None, ge=0, le=1e9)
    cost_currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    cost_basis: str | None = Field(default=None, min_length=3, max_length=300)

    @model_validator(mode="after")
    def physical(self):
        if self.bottom_md_m <= self.top_md_m:
            raise ValueError("Casing bottom must exceed top MD.")
        nominal_wall = (self.outside_diameter_m - self.inside_diameter_m) / 2
        if nominal_wall <= 0 or self.minimum_wall_m > nominal_wall + 1e-9:
            raise ValueError("Casing ID must be below OD and minimum wall cannot exceed nominal wall.")
        if self.minimum_wall_m - self.wall_loss_allowance_m < 1e-5:
            raise ValueError("Wall-loss allowance must leave at least 0.01 mm wall for numerical eligibility; this is not an operating limit.")
        if any(getattr(self, k) is not None for k in ("yield_strength_pa", "body_burst_pa", "body_collapse_pa", "body_tension_n", "body_compression_n")) and not self.body_rating_source:
            raise ValueError("Body properties require a traceable rating source.")
        if any(getattr(self, k) is not None for k in ("connection_burst_pa", "connection_collapse_pa", "connection_tension_n", "connection_compression_n")) and not self.connection_rating_source:
            raise ValueError("Connection properties require a traceable rating source.")
        if self.cost_per_m is not None and (not self.cost_currency or not self.cost_basis):
            raise ValueError("Cost requires a currency and price basis.")
        return self


class GeometryInput(Contract):
    survey_dataset_id: str = Field(min_length=1, max_length=80)
    datum: str = Field(min_length=1, max_length=100)
    coordinate_reference: str = Field(min_length=3, max_length=200)
    wellhead_north_m: float = Field(ge=-1e8, le=1e8)
    wellhead_east_m: float = Field(ge=-1e8, le=1e8)
    wellhead_elevation_m: float = Field(ge=-10000, le=10000)
    survey_quality_note: str = Field(min_length=3, max_length=300)
    tool_to_bit_offset_m: float = Field(ge=0, le=100)
    formations: list[InterpretedTop] = Field(default_factory=list, max_length=100)
    hole_sections: list[HoleSection] = Field(default_factory=list, max_length=100)
    casings: list[CasingRecord] = Field(default_factory=list, max_length=30)

    @model_validator(mode="after")
    def unique_ordered(self):
        for collection in (self.formations, self.hole_sections, self.casings):
            if len({x.name.casefold() for x in collection}) != len(collection):
                raise ValueError("Record names must be unique within each geometry category.")
        if any(b.top_tvd_m <= a.top_tvd_m for a, b in zip(self.formations, self.formations[1:])):
            raise ValueError("Formation tops must strictly increase in TVD; use separate scenarios for alternatives.")
        if self.hole_sections:
            if self.hole_sections[0].top_md_m != 0:
                raise ValueError("Hole sections must start at MD 0.")
            if any(abs(a.bottom_md_m - b.top_md_m) > 1e-6 for a, b in zip(self.hole_sections, self.hole_sections[1:])):
                raise ValueError("Hole sections must be ordered and contiguous, without overlap or gaps.")
        return self


class GeometryRevisionRequest(Contract):
    base_revision_id: str | None = None
    change_note: str = Field(min_length=3, max_length=500)
    geometry: GeometryInput


class Path:
    def __init__(self, survey: SurveyRequest):
        self.stations = survey.stations
        self.rows = minimum_curvature(survey)
        self.depths = [s.md_m for s in self.stations]

    def segment(self, i):
        a, b = self.stations[i:i+2]
        va = [math.sin(a.inclination_rad)*math.cos(a.azimuth_rad),
              math.sin(a.inclination_rad)*math.sin(a.azimuth_rad), math.cos(a.inclination_rad)]
        vb = [math.sin(b.inclination_rad)*math.cos(b.azimuth_rad),
              math.sin(b.inclination_rad)*math.sin(b.azimuth_rad), math.cos(b.inclination_rad)]
        beta = math.acos(max(-1., min(1., sum(x*y for x, y in zip(va, vb)))))
        return a, b, va, vb, beta

    def at(self, md):
        if not math.isfinite(md) or md < 0 or md > self.depths[-1]:
            raise ValueError("Requested MD is outside the accepted survey.")
        i = max(0, min(len(self.stations)-2, bisect.bisect_right(self.depths, md)-1))
        a, b, va, vb, beta = self.segment(i)
        t = (md-a.md_m)/(b.md_m-a.md_m)
        if beta < 1e-7:
            delta = [(b.md_m-a.md_m)*(t*x + .5*t*t*(y-x)) for x,y in zip(va,vb)]
        else:
            u = [(y-x*math.cos(beta))/math.sin(beta) for x,y in zip(va,vb)]
            delta = [(b.md_m-a.md_m)*(x*math.sin(beta*t) + y*2*math.sin(beta*t/2)**2)/beta for x,y in zip(va,u)]
        return {"md_m": md, **{key:self.rows[i][key]+d for key,d in zip(("north_m","east_m","tvd_m"),delta)}}

    def coincident_intervals(self, tvd):
        intervals=[]
        for a,b in zip(self.stations,self.stations[1:]):
            if all(abs(self.at(md)["tvd_m"]-tvd)<1e-7 for md in (a.md_m,(a.md_m+b.md_m)/2,b.md_m)):
                if intervals and abs(intervals[-1]["bottom_md_m"]-a.md_m)<1e-6:
                    intervals[-1]["bottom_md_m"]=b.md_m
                else:
                    intervals.append({"top_md_m":a.md_m,"bottom_md_m":b.md_m})
        return intervals

    def intersections(self, tvd):
        found = []
        for i in range(len(self.stations)-1):
            a,b,va,vb,beta = self.segment(i)
            cuts = [a.md_m,b.md_m]
            if beta >= 1e-7:
                uz = (vb[2]-va[2]*math.cos(beta))/math.sin(beta)
                angle = math.atan2(-va[2],uz)
                for k in range(-1,3):
                    x = angle+k*math.pi
                    if 0 < x < beta:
                        cuts.append(a.md_m+(b.md_m-a.md_m)*x/beta)
            cuts.sort()
            for lo,hi in zip(cuts,cuts[1:]):
                flo,fhi = self.at(lo)["tvd_m"]-tvd,self.at(hi)["tvd_m"]-tvd
                if abs(flo) < 1e-7:
                    found.append(lo)
                if abs(fhi) < 1e-7:
                    found.append(hi)
                if flo*fhi < 0:
                    for _ in range(55):
                        mid=(lo+hi)/2
                        fm=self.at(mid)["tvd_m"]-tvd
                        if flo*fm <= 0:
                            hi=mid
                        else:
                            lo=mid; flo=fm
                    found.append((lo+hi)/2)
        unique=[]
        for md in sorted(found):
            if not unique or abs(md-unique[-1]) > 1e-5:
                unique.append(md)
        contacts=self.coincident_intervals(tvd)
        return [self.at(md) for md in unique if not any(c["top_md_m"]-1e-6 <= md <= c["bottom_md_m"]+1e-6 for c in contacts)]


def geometry_result(data: GeometryInput, survey: SurveyRequest):
    path = Path(survey)
    td = path.depths[-1]
    for h in data.hole_sections:
        if h.bottom_md_m > td + 1e-6:
            raise ValueError("Hole section extends beyond the accepted survey.")
    for c in data.casings:
        if c.bottom_md_m > td + 1e-6:
            raise ValueError("Casing extends beyond the accepted survey.")
        covered = sum(max(0,min(c.bottom_md_m,h.bottom_md_m)-max(c.top_md_m,h.top_md_m)) for h in data.hole_sections)
        if abs(covered-(c.bottom_md_m-c.top_md_m)) > 1e-6:
            raise ValueError("Every casing interval requires complete hole geometry.")
        for h in data.hole_sections:
            if max(c.top_md_m,h.top_md_m) < min(c.bottom_md_m,h.bottom_md_m) and c.outside_diameter_m >= h.diameter_m:
                raise ValueError("Casing OD must clear every intersected hole section.")
    for i,a in enumerate(data.casings):
        for b in data.casings[i+1:]:
            if max(a.top_md_m,b.top_md_m) < min(a.bottom_md_m,b.bottom_md_m):
                outer,inner=sorted((a,b),key=lambda c:c.outside_diameter_m,reverse=True)
                if inner.outside_diameter_m >= outer.inside_diameter_m:
                    raise ValueError("Overlapping casing strings have incompatible radial clearance.")
    # Include section boundaries and original stations as well as regular MD samples.
    points=set(path.depths)
    spacing=max(25.,td/1000.)
    points.update(min(td,i*spacing) for i in range(math.ceil(td/spacing)+1))
    for c in [*data.hole_sections,*data.casings]:
        points.update((c.top_md_m,c.bottom_md_m))
    samples=[]
    for md in sorted(points):
        p=path.at(md)
        samples.append({**p,"reference_north_m":p["north_m"]+data.wellhead_north_m,
                        "reference_east_m":p["east_m"]+data.wellhead_east_m,
                        "elevation_m":data.wellhead_elevation_m-p["tvd_m"]})
    intersections=[{"name":f.name,"category":f.category,"origin":f.interpretation,"source":f.source,
                    "top_tvd_m":f.top_tvd_m,"uncertainty_m":f.uncertainty_m,
                    "top_crossings":path.intersections(f.top_tvd_m), "coincident_intervals":path.coincident_intervals(f.top_tvd_m),
                    "shallow_band_crossings":path.intersections(f.top_tvd_m-f.uncertainty_m),
                    "deep_band_crossings":path.intersections(f.top_tvd_m+f.uncertainty_m)} for f in data.formations]
    currencies={c.cost_currency for c in data.casings if c.cost_per_m is not None}
    cost_complete=bool(data.casings) and len(currencies)==1 and all(c.cost_per_m is not None for c in data.casings)
    warnings=[]
    if not data.hole_sections or data.hole_sections[-1].bottom_md_m < td:
        warnings.append("Hole geometry does not cover the full survey.")
    if data.tool_to_bit_offset_m:
        warnings.append("Path represents survey stations. Tool-to-bit offset is recorded, not extrapolated to a bit trajectory.")
    return {"model":"minimum-curvature-geometry","version":"0.2.0","status":"conditional",
            "samples":samples,"formation_intersections":intersections,"warnings":warnings,
            "total_depth_md_m":td,"survey_station_count":len(path.rows),
            "cost": {"status":"conditional" if cost_complete else "insufficient_data",
                     "value":sum((c.bottom_md_m-c.top_md_m)*c.cost_per_m for c in data.casings) if cost_complete else None,
                     "currency":next(iter(currencies)) if cost_complete else None,
                     "scope":"Pipe-length costs only; excludes connections, installation, cement and logistics."},
            "assumptions":["Formation boundaries are interpreted horizontal TVD surfaces; bands are supplied pick uncertainty, not confidence intervals.",
                           "Coordinates are translated into the declared frame; no CRS, magnetic or grid-convergence transformation.",
                           "Survey uncertainty is not quantified; interpreted geology does not confirm isolation or collision clearance."]}
