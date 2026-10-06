# FORGE dynamics source review — 6 October 2026

The [original GDR record](https://gdr.openei.org/submissions/1283) lists drilling
series at one-second and ten-second intervals. These intervals alone cannot
establish raw downhole acceleration bandwidth, calibration or anti-alias filtering.
Their respective Nyquist limits are 0.5 Hz and 0.05 Hz; they cannot establish the
claimed 14–18 Hz axial band from sampled raw signals.

[Gentry et al. (2023), page 8](https://pangea.stanford.edu/ERE/pdf/IGAstandard/SGW/2023/Gentry.pdf)
report that their FORGE study had processed vibration values and lacked raw,
high-frequency vibration data. This is a documented limitation of that study,
not proof that no other native dataset exists. Their reported machine-learning
accuracy does not validate this application's BHA model or embedded targets.

The embedded 0.28 Hz torsional target, severity value and 14–18 Hz axial band
still have no verified file/row extraction. Required inputs remain native sensor
records, timebase, instrument calibration, anti-alias filtering, matching BHA
geometry/boundaries and independent holdout observations. The acquired survey
workbook supplies directional coordinates, not these vibration observations.

For cuttings transport, the [publisher's journal listing](https://onepetro.org/DC/issue/12/02)
identifies Larsen, Pilehvari and Azar's article as DOI 10.2118/25872-PA. The previous
SPE-27490 attribution has not been verified as the origin of the embedded table.
No experimental table or reproduction license has been acquired; the example's
fit to its own targets remains outside independent production-model validation.
