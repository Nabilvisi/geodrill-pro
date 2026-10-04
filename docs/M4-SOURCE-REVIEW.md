# M4 source review and selected implementation

Primary source located on 3 October 2026: Maria Bala, Evaluation of shale distribution in shaly-sand rocks on the basis of well logging data - the crossplots method, Geology, Geophysics and Environment 36(2), 2010, DOI 10.7494/geol.2010.36.2.223.
Article: https://journals.agh.edu.pl/geol/article/view/301
PDF: https://journals.agh.edu.pl/geol/article/download/301/204/705

This is a later application of Thomas and Stieber's SPWLA 1975 paper T, not a replacement for the original formulation or an independent engineering approval.

Implementation review targets:

- Audit section 5.4 permits the simple laminated volume identities as verification cases, and explicitly distinguishes them from the complete Thomas-Stieber model.
- The paper's table on PDF page 6 gives synthetic clean-sand GR/porosity 20 API/0.30, shale 100 API/0.15, and filled dispersed-sand endpoint 50 API/0.0614.
- Equations 1 and 2 and their definitions must be visually checked from the PDF before transcription; text extraction has damaged mathematical symbols.
- The sonic example uses matrix/fluid/dispersed-shale transit times 170/610/520 microseconds per metre. Its apparent sonic porosity convention must be distinguished from total and effective physical porosity.
- Do not equate the supplied shale porosity endpoint to a transit-time-derived porosity without checking that the basis is compatible.
- The gamma relation in this published example includes a constant background; do not silently substitute a different normalized-GR volume model.
- Acquire exact structural/dispersed definitions, admissibility and reference cases before representing a full model. Any narrower implementation must state its variant and remaining scope.
- No source supplies a universal GR-to-clay conversion or automatic topology acceptance.

Version 0.3.0 implements the separately defined wet-shale/primary-pore construction documented in MODEL-SPECS-0.3.md. Its primary reference is the published background construction in AU2013315927B2, paragraphs 0008–0011: https://patents.google.com/patent/AU2013315927B2/en. It covers laminated/dispersed/structural volume scenarios and explicit coexisting-texture alternatives. The Bala apparent-sonic variant remains excluded because its measurement convention must not be silently equated to physical total porosity. Numerical and browser checks are recorded in VERIFICATION.md; independent specialist approval remains open.
