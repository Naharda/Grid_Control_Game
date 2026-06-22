# Translated Instructions
## Faculty of Computer and Information Sciences
### 237-2-5513 Search Methods in Artificial Intelligence

**Project Submission Guidelines**
The goal of the project is for students to conduct practical research work on one of the topics taught in class and submit a lab report detailing the research, its results, and conclusions. It can be submitted in pairs only. A typical lab report will include the chapters detailed below. However, the course encourages creativity, and therefore, if your project is better presented in a different report structure, you are welcome to alter it.

**Introduction and Literature Review**
This chapter aims to present the background to the topic of the work, explain the motivation for its selection, and clearly define the problem or research objective. Additionally, the chapter should include a comprehensive literature review of relevant works, papers, and methods from the field, while comparing existing approaches and highlighting the contribution or uniqueness of the project. The chapter is graded, among other factors, based on the quality and scope of the literature review, the level of understanding and analysis of the sources, the presentation of a well-reasoned and clear motivation, the correct and consistent use of citations and bibliography, as well as organization, clarity, and proper academic writing.

**Methodology**
This chapter is intended to describe in an organized and detailed manner the working methods and tools used during the project. The chapter needs to explain the development or research process, the choice of algorithms, technologies, data structures, working environment, and the selected testing or evaluation methods, while justifying the choices made. Additionally, the implementation stages, the method of data collection or processing if necessary, and the manner of evaluating the system's results must be described. The chapter is graded based on the level of detail and clarity, the suitability of the methodology to the project's objectives, professional justification for technical choices, and the ability to present a consistent and reproducible workflow.

**Experimental Results**
This chapter is intended to present the findings of the project and the experiments conducted in a clear and organized manner. The chapter includes presenting the data using relevant tables, graphs, and charts, alongside an explanation and analysis of the obtained results. Additionally, it must detail what can be inferred from the results, how they support (or refute) the project's objectives or the hypotheses tested, and what their significance is in relation to previous methods or works. The chapter is graded based on the quality of the data presentation, the clarity of the graphs and tables, the depth of the analysis and discussion of the results, and the ability to draw evidence-based conclusions.

**Experimental Conclusions and Summary**
This chapter aims to consolidate all the findings of the project and present a comprehensive picture of the results relative to the objectives defined at the beginning of the work. In this chapter, the main work performed is summarized, the central contribution of the project is emphasized, and the conclusions derived from the experimental results and the analysis conducted are presented. Additionally, it is required to address whether the project's objectives were achieved, what can be learned from the results, and what limitations were discovered during the work. It is also common to suggest future directions or improvements. The chapter is graded based on the clarity and phrasing of the conclusions, a direct connection to the project's objectives, the depth of overall understanding and analysis, the ability to present a coherent summarizing picture, as well as the level of critical thinking and the proposal of future directions. Note that this chapter is usually shorter than the rest.

Additionally, the report must include a link to the code you used for the purpose of running the experiments and preparing the graphs in the project.

**Report Format**
It is recommended to use the AAAI '27 format in order to write the report in a Camera Ready version, though other formats may be used. It is advisable to use the `\nocopyright` command to remove the footnote on the first page. The format files can be found here (link to the general site).

**Choosing a Project Idea**
Choosing an idea for a final project can be based on one or more of the following directions:
* Replicating and implementing an existing paper, adapting it to a new domain that was not originally examined, and evaluating the method's performance under conditions different from the original research.
* Proposing a change, extension, or improvement to an existing algorithm (for example, an evaluation function, expansion strategy, or search mechanism), provided there is a clear motivation for the change and its contribution can be experimentally evaluated.
* Choosing a completely new domain and conducting comprehensive tests of existing heuristic search algorithms on it, including a comparison between different methods, performance analysis, and drawing conclusions.

Below are several possible ideas for projects. This list is not exhaustive, and it is possible and even desirable to propose additional ideas:
* Comparing SFBDS with the F2F heuristic against F2E.
* Replicating the error model of Explicit Estimation Search and reproducing the paper's results (specifically the 15-Puzzle).
* Testing different Best-First Search algorithms on the "Sorting Colored Balls in Colored Tubes" problem.
* Fixing the PEA*+IDA* paper to also account for CLOSED when checking the memory bound and comparing against the results reported in the paper.
* Learning a heuristic function using a neural network (here, supervised or reinforcement learning can be used).
* Testing bidirectional search algorithms in Voxel Benchmarks for 3D Pathfinding.
* Replicating the WMM anomaly on the domains tested in the paper and additional domains.
* Parallelizing existing algorithms that do not yet have a parallel version.
* Testing different node prioritization functions in bounded suboptimal and unbounded suboptimal search within the context of a single function as well as within a Focal Search structure.
* Creating a search-based agent for a strategy game and comparing it against a threshold metric such as a random, rule-based, or human agent, etc. Please avoid popular games such as Chess, Checkers, Connect Four, and Backgammon. Interesting games that can be tried include Abalone, Attax, Ultimate Tic-Tac Toe, and more.

However, there are a number of ideas that are liable to receive a low grade since they are highly common, relatively simple to implement, possess limited uniqueness, and provide a minimal contribution in terms of innovation or research interest:
* Comparing A* against IDA* on popular domains in the literature.
* Comparing BFS against DFS.
* Comparing Minimax against Alpha-Beta pruning.



# Scratch

## Deciding the project idea

1. Testing bidirectional search algorithms in Voxel Benchmarks for 3D Pathfinding.
	- **Why Reder likes this idea:** If it's a known benchmark that's been tested on, we have plenty of references for the evaluation, metrics, etc. likely even in code, and Claude could do an amazing job replicating these data formats without much intervention
2. Parallelizing existing algorithms that do not yet have a parallel version.
	- **Why Reder:** IDK just sounds awfully simple, a little bit of research into evaluation metrics and how to implement, but sounds straightforward enough
3. Creating a search-based agent for a strategy game and comparing it against a threshold metric such as a random, rule-based, or human agent, etc. Please avoid popular games such as Chess, Checkers, Connect Four, and Backgammon. Interesting games that can be tried include Abalone, Attax, Ultimate Tic-Tac Toe, and more.
	- **Why Omri:** Doesn't sound too hard, it's all about finding a "pathfinding-able" game and a reasonable\self-explanatory heuristic for it 