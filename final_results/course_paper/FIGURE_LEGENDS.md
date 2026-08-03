# Figure legends

## Figure 1

**Figure 1: Turn structure and capture modes.** **(A)** The player selects a public card, acts, scores, refills the market randomly, and tests the stopping rule. With no legal card the player passes; two passes refresh the market. **(B)** The five card types and their ranges. Mobilize moves two pieces when possible and otherwise one. **(C)** A regular (melee) capture targets an orthogonally adjacent enemy. A net launcher uses an adjacent friendly pair and the first occupied cell on an outward range-3 ray. Both score three points and respawn the target; objective cells score at turn end. Blue is the acting side and red the target; diagrams are schematic.

## Figure 2

**Figure 2: Three board geometries define the spatial experimental factor.** **(A)** Default open 5x5 board. **(B)** Bottleneck 7x7 board with blocked central lanes. **(C)** Inner-ring 7x7 board with more widely separated spawns and a four-point center. Blue and red circles mark the initial cells of players A and B; yellow cells are end-of-turn objectives labeled by points; dark cells are blocked. Coordinates and piece identities are omitted because the JSON board definitions are the authoritative executable specification.

## Figure 3

**Figure 3: Agent rankings vary across board geometry and stopping rule.** **(A-C)** Win points for the six agents on the default, bottleneck, and inner-ring boards, respectively. Columns are a fixed 25-turn-per-player horizon and point goals of 10 or 40; the turn cap remains a safety bound in goal games. Each cell contains 30 agent-game observations: five opponents, both player orders, and three matched seeds. A win contributes 1, a draw 0.5, and a loss 0. Color and printed values both encode win points (%); 50% denotes parity across opponents. Conditions are separate tests, not pooled replicates.

## Figure 4

**Figure 4: Additional computation does not yield a monotonic performance gain.** **(A)** Aggregate win points versus weighted mean decision time across the 12 main and independent-deck conditions. Each agent has 360 agent-game observations; time is total recorded decision time divided by non-pass decisions and is shown on a logarithmic axis. The dashed line marks 50% win points. **(B)** First-seat minus second-seat win-points rate for the same conditions (180 agent-game observations per seat and agent). Positive values favor moving first. Colors identify agents in both panels; labels provide a redundant non-color encoding.

## Figure 5

**Figure 5: Independently changing deck composition shifts relative agent performance.** **(A)** Counts of the five action cards in each 28-card deck; stacked segments sum to 28. **(B)** Win points on the default board under the fixed 25-turn-per-player horizon. Each cell contains 30 agent-game observations across five opponents, both player orders, and three matched seeds. Color and printed values encode win points (%). The default condition is the shared control; the three alternatives change only card counts while retaining the two-pass market refresh.

## Figure 6

**Figure 6: Deeper expectimax is substantially slower and is not uniformly stronger.** **(A)** Depth-3 win points in direct depth-3 versus depth-2 matches for all nine board/stopping-rule combinations. Each cell summarizes six games (three matched seeds in both player orders); 50% denotes parity. **(B-C)** Weighted mean decision time and win points, respectively, in the bounded goal-20 feasibility study. Bars summarize six agent-game observations per board and depth; all variants use a top-2 action cap. Runtime uses a logarithmic axis and the dashed performance line marks 50%. Depth 4 used one seed and is interpreted as a feasibility measurement; depth 5 exceeded 120 s for one benchmark decision and depth 6 was not run.

## Figure 7

**Figure 7: Net launches are a recurring but minority capture mode.** **(A)** Adjacent and net-launcher capture actions reconstructed from all per-turn logs in the 1,080-game main and deck suite (7,863 captures; 1,729 net launches). Counts are events, not games, and therefore reflect both opportunity and agent behavior. **(B)** Net launches as a percentage of each agent's captures, with exact percentages printed beside the bars. Expectimax depth 4 is excluded because it appears only in the smaller bounded feasibility study. Across the displayed agents, the net share ranges from 19.3% (Expectimax d3) to 27.5% (Random).
