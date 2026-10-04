"""Imported EM interpretation review; no local forward model or inversion."""
from datetime import datetime
from typing import Literal
from pydantic import Field, model_validator
from .models import Contract

def instant(text: str):
    try:
        value = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("Acquisition and receipt times must be ISO-8601 timestamps.")
    if value.utcoffset() is None:
        raise ValueError("Acquisition and receipt timestamps require an explicit UTC offset.")
    return value

class SuppliedInterval(Contract):
    lower: float
    upper: float
    meaning: str = Field(min_length=3, max_length=300)
    @model_validator(mode="after")
    def ordered(self):
        if self.lower > self.upper:
            raise ValueError("Supplied interval lower bound exceeds upper bound.")
        return self

class EMSample(Contract):
    md_m: float = Field(ge=0, le=30000)
    acquired_at: str = Field(min_length=10, max_length=50)
    received_at: str | None = Field(default=None, min_length=10, max_length=50)
    rh_ohm_m: float | None = Field(default=None, gt=0, le=1e7)
    rv_ohm_m: float | None = Field(default=None, gt=0, le=1e7)
    rh_interval: SuppliedInterval | None = None
    rv_interval: SuppliedInterval | None = None
    boundary_distance_m: float | None = Field(default=None, ge=-10000, le=10000)
    boundary_interval: SuppliedInterval | None = None
    boundary_reference: str | None = Field(default=None, min_length=3, max_length=300)
    quality: Literal["vendor_usable", "vendor_rejected", "unknown"]
    quality_note: str = Field(min_length=3, max_length=300)
    misfit: float | None = Field(default=None, ge=0, le=1e12)
    misfit_definition: str | None = Field(default=None, min_length=3, max_length=300)
    @model_validator(mode="after")
    def evidence(self):
        acquired=instant(self.acquired_at)
        if self.received_at and instant(self.received_at) < acquired:
            raise ValueError("Receipt time cannot precede acquisition.")
        for name in ("rh", "rv"):
            estimate=getattr(self, name+"_ohm_m")
            interval=getattr(self, name+"_interval")
            if interval and (estimate is None or interval.lower <= 0 or interval.upper > 1e7 or not interval.lower <= estimate <= interval.upper):
                raise ValueError("Resistivity intervals require a positive estimate inside the supplied bounds.")
        if self.boundary_distance_m is not None and self.boundary_reference is None:
            raise ValueError("Boundary distance requires a supplied reference point, direction and sign convention.")
        if self.boundary_interval and (self.boundary_distance_m is None or self.boundary_interval.lower < -10000 or self.boundary_interval.upper > 10000 or not self.boundary_interval.lower <= self.boundary_distance_m <= self.boundary_interval.upper):
            raise ValueError("Boundary interval requires an estimate inside its bounds.")
        if self.misfit is not None and not self.misfit_definition:
            raise ValueError("Misfit requires its supplied statistic, units and normalization definition.")
        return self

class EMTool(Contract):
    vendor: str = Field(min_length=3, max_length=100)
    tool: str = Field(min_length=3, max_length=100)
    processing_version: str = Field(min_length=1, max_length=100)
    frequencies_hz: list[float] = Field(max_length=24)
    transmitter_receiver_spacings_m: list[float] = Field(max_length=24)
    geometry_orientation_note: str = Field(min_length=3, max_length=1000)
    tool_to_bit_offset_m: float | None = Field(default=None, ge=0, le=300)
    model_dimension: Literal["1D", "2D", "3D", "unknown"]
    forward_model_reference: str = Field(min_length=3, max_length=500)
    calibration_environment_note: str = Field(min_length=3, max_length=1000)
    priors_regularization_note: str = Field(min_length=3, max_length=1000)
    uncertainty_nonuniqueness_note: str = Field(min_length=3, max_length=1000)
    qualification_reference: str | None = Field(default=None, min_length=3, max_length=500)
    @model_validator(mode="after")
    def instrument(self):
        if any(not 0 < x <= 1e9 for x in self.frequencies_hz) or any(not 0 < x <= 300 for x in self.transmitter_receiver_spacings_m):
            raise ValueError("Declared frequencies and antenna spacings must be positive and within the numerical envelope.")
        return self

class EMVendorDocument(Contract):
    schema_version: Literal["geodrill-em-vendor-1"]
    origin: Literal["synthetic", "historical"]
    well_name: str = Field(min_length=1, max_length=100)
    depth_datum: str = Field(min_length=1, max_length=100)
    resistivity_unit: Literal["ohm.m"]
    boundary_distance_unit: Literal["m"]
    source_reference: str = Field(min_length=3, max_length=500)
    data_rights_note: str = Field(min_length=3, max_length=500)
    tool: EMTool
    samples: list[EMSample] = Field(min_length=1, max_length=1000)
    @model_validator(mode="after")
    def native_order(self):
        if any(b.md_m <= a.md_m for a,b in zip(self.samples,self.samples[1:])):
            raise ValueError("Native measured depths must strictly increase; repeated passes require separate source files.")
        return self

class EMReviewInput(Contract):
    study_name: str = Field(min_length=3, max_length=100)
    dataset_id: str = Field(min_length=1, max_length=80)
    geometry_revision_id: str = Field(min_length=1, max_length=80)
    depth_datum: str = Field(min_length=1, max_length=100)
    alignment_status: Literal["supplied_confirmed", "unverified"]
    md_offset_m: float = Field(ge=-1000, le=1000)
    depth_alignment_note: str = Field(min_length=3, max_length=500)
    reviewer_note: str = Field(min_length=3, max_length=1000)

def review_vendor(document: EMVendorDocument, value: EMReviewInput, total_depth_m: float):
    if document.depth_datum != value.depth_datum:
        raise ValueError("Document and review datum differ; an MD offset does not authorize a datum conversion.")
    rows=[]
    for i,s in enumerate(document.samples):
        aligned=s.md_m+value.md_offset_m
        reasons=[]
        if value.alignment_status != "supplied_confirmed":
            reasons.append("Depth alignment is unverified.")
        if not 0 <= aligned <= total_depth_m:
            reasons.append("Aligned measured depth is outside the saved survey.")
        if s.quality != "vendor_usable":
            reasons.append("Vendor sample quality is rejected or unknown.")
        if s.rh_ohm_m is None and s.rv_ohm_m is None and s.boundary_distance_m is None:
            reasons.append("No supplied interpreted value.")
        eligible=not reasons
        derived={
            "rh_ohm_m":s.rh_ohm_m,"rv_ohm_m":s.rv_ohm_m,
            "boundary_distance_m":s.boundary_distance_m,
            "rh_interval":s.rh_interval.model_dump() if s.rh_interval else None,
            "rv_interval":s.rv_interval.model_dump() if s.rv_interval else None,
            "boundary_interval":s.boundary_interval.model_dump() if s.boundary_interval else None,
            "boundary_reference":s.boundary_reference,
        } if eligible else None
        rows.append({"source_index":i,"native_md_m":s.md_m,"aligned_md_m":aligned,
                     "status":"imported_vendor_result" if eligible else "withheld",
                     "reasons":reasons,"supplied":s.model_dump(),"display":derived,
                     "receipt_delay_s":(instant(s.received_at)-instant(s.acquired_at)).total_seconds() if s.received_at else None})
    eligible=sum(r["display"] is not None for r in rows)
    missing_uncertainty=sum(r["display"] is not None and any(getattr(document.samples[r["source_index"]],k+"_ohm_m") is not None and getattr(document.samples[r["source_index"]],k+"_interval") is None for k in ("rh","rv")) for r in rows)
    readiness={
        "declared_frequencies":bool(document.tool.frequencies_hz),
        "declared_antenna_spacings":bool(document.tool.transmitter_receiver_spacings_m),
        "declared_tool_to_bit_offset":document.tool.tool_to_bit_offset_m is not None,
        "supplied_qualification_reference":document.tool.qualification_reference is not None,
        "raw_measurement_interface":False,"independent_forward_model_verified":False,
        "inversion_benchmarks_verified":False,
    }
    return {"model":"imported-vendor-em-review","model_version":"0.1.0",
            "status":"vendor_result_display" if eligible else "withheld",
            "eligible_count":eligible,"withheld_count":len(rows)-eligible,
            "missing_resistivity_interval_count":missing_uncertainty,
            "origin":document.origin,"tool":document.tool.model_dump(),
            "source_reference":document.source_reference,"data_rights_note":document.data_rights_note,
            "integration_readiness":readiness,"native_inversion_available":False,
            "interpretation_approved":False,"steering_authority":"none","rows":rows,
            "warnings":[
                "Supplied vendor interpretations are displayed; GeoDrill does not perform an EM inversion or validate the vendor model.",
                "Intervals, quality, misfit and qualification references are supplied evidence, not independent validation or calibrated confidence.",
                "Receipt delay is receipt minus acquisition, not guaranteed telemetry latency, computation time or tool cadence.",
                "MD offset only aligns declared native MD; tool-to-bit spacing is preserved separately and never applied automatically.",
                "Boundary distances keep their supplied reference and sign convention; they are not converted into surfaces or look-ahead claims.",
                "Missing values and withheld samples are not filled, interpolated or connected in plots.",
            ]}
