# Figure layout selection and audit

All figures target a two-column AAAI-like page at a final width of approximately 7.16 inches. Scores use the publication-figure skill's weighted 1-5 rubric. The selected layouts clearly dominated because the alternatives either repeated the original crowding problem or obscured denominators; therefore layout selection did not require pausing for user input.

| Figure | Candidate | Layout | Score / 5 | Decision and trade-off |
|---|---|---|---:|---|
| 1 | Narrative-first | Turn sequence, card glossary, and two framed capture modes with scoring | 4.8 | **Selected.** Regular and net captures are directly contrasted while each phrase remains inside its box at final size. |
| 1 | Single workflow | One long flowchart including boards and all rules | 2.7 | Rejected: reproduces the original overflow and forces unreadably small text. |
| 2 | Comparison-first | Three equal-scale board panels | 4.8 | **Selected.** Direct geometry comparison with identical visual language. |
| 2 | One annotated composite | Overlay all board features in one schematic | 2.9 | Rejected: spatial differences and objective values become ambiguous. |
| 3 | Comparison-first | Three matched annotated heatmaps | 4.6 | **Selected.** Displays all 54 condition-agent cells compactly with exact values. |
| 3 | Grouped bars | Six agents grouped within every condition | 3.2 | Rejected: 54 narrow bars and repeated legends reduce final-size readability. |
| 4 | Result-first | Log runtime-performance scatter plus seat-effect bars | 4.6 | **Selected.** Separates efficiency from order while sharing agent encodings. |
| 4 | Three-table summary | Runtime, win rate, and seat effect in adjacent tables | 3.5 | Rejected: exact but weak visual support for the non-monotonic relationship. |
| 5 | Manipulation-to-result | Deck composition stacked bars followed by performance heatmap | 4.7 | **Selected.** Shows both the controlled manipulation and its outcomes. |
| 5 | Performance only | Heatmap without card counts | 3.4 | Rejected: readers cannot see what each deck label means. |
| 6 | Evidence-chain | Direct head-to-head heatmap, runtime bars, bounded-performance bars | 4.5 | **Selected.** Distinguishes the robust matched comparison from the small feasibility study. |
| 6 | Runtime curve | Connected depth-runtime lines | 3.0 | Rejected: connecting three discrete depths implies unsupported interpolation. |
| 7 | Denominator-aware | Capture counts plus within-agent net shares | 4.7 | **Selected.** Prevents normalized shares from hiding unequal event counts. |
| 7 | Shares only | One percentage bar chart | 3.5 | Rejected: omits the event denominators needed for interpretation. |

## Final preflight

- All seven standalone PNG previews and vector PDF exports were inspected.
- The assembled seven-page paper was rendered at 150 dpi and every page was inspected at full size; short article sections were balanced across columns and orphaned lines were removed.
- No panel label touches a title; no text leaves a box; no heatmap cell or color scale is obscured.
- Figures preserve their native aspect ratios in the assembled paper.
- All axes state the quantity and unit, and every color scale is labeled.
- Panel letters are consecutive and legends follow visual order.
- Source values were regenerated from the validated result tables; the report contains no simulated quantitative panel. Figure 7 uses the comparable 1,080-game main/deck cohort (7,863 captures, including 1,729 net launches; 22.0%), while the distinct full-suite total is 1,769/8,020 (22.1%) and is identified separately in the Results text.
- Figure 1C separately frames and labels regular capture and net launcher; its explanatory text remains inside the panel. Figure 4's point labels are separated; Figures 5 and 6 place legends below the data panels; Figure 7's legend clears the plotting region.
- Figure 2's bottleneck subtitle was checked against `boards/bottleneck_7x7.json` and reports the three objective values as +1/+3/+1.
- The assembled paper contains seven nonblank pages with no clipping, legend/data overlap, or unintended blank page.
- The `graph_card_control_course_paper.pdf` and `graph_card_control_final_report.pdf` output names are byte-identical aliases of the same current manuscript, preventing the superseded Figure 1 from appearing under the older filename.
