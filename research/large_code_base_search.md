## Building Agents, Large code base agentic search, and model understanding given context window constraints

### Reading list... Posts, Papers and Videos consumed:
---
[Open AI guide to building agents](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)
[Anthropic guide to building agents](https://www.anthropic.com/engineering/building-effective-agents)
[Anthropic guide to building multi agent systems](https://www.anthropic.com/engineering/multi-agent-research-system)
[Manus - Context Engineering for Agents](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)
[Lance Martin - Context engineering for Agents](https://rlancemartin.github.io/2025/06/23/context_engineering/)
[Lance Martin - Learning the Bitter Lesson](https://rlancemartin.github.io/2025/07/30/bitter_lesson/)
[Huong Won Chung - OpenAI - Stanford talk on doing AI research](https://www.youtube.com/watch?v=orDKvo8h71o)
[The state of AI Agents - Lance Martin](https://rlancemartin.github.io/2025/06/10/aie/)
[Hugging Face - Open source Deep Research](https://huggingface.co/blog/open-deep-research#:~:text=From%20building%20,it%20can%20still%20use%20it)
[Cognition - Don't build multi-agent systems](https://cognition.ai/blog/dont-build-multi-agents#principles-of-context-engineering)
[Simon Willison on the Anthropic post of multi agent systems](https://simonwillison.net/2025/Jun/14/multi-agent-research-system/)
[Simon Willison on tracing Claude to understand its agentic props](https://simonwillison.net/2025/Jun/2/claude-trace/)
[Link to Open Deep Research - Lance Martin](https://github.com/langchain-ai/open_deep_research)
[LIMI paper - 78 carefully chosen examples improves LLM responses dramatically](https://arxiv.org/pdf/2509.17567)
[X post summarizing LIMI paper](https://x.com/rohanpaul_ai/status/1970827405297082385?s=12)
[Author of ripgrep - deep explanation of design choices for file searching](https://burntsushi.net/ripgrep/#gathering-files-to-search)
[Context Engineering for Agents - Lance Martin on Latent Space](https://www.youtube.com/watch?v=_IlTcWciEC4)
[Drew Bruenig on how Long Contexts Fail](https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html)
[Gemini youtube url api](https://ai.google.dev/gemini-api/docs/video-understanding#youtube)
[The Prompt Report: A Systematic Survey of Prompt Engineering Techniques](https://arxiv.org/pdf/2406.06608)
---

## Some high level ideas garnered from the above:
1. The GEPA paper is extremely compelling for using [DSPY](https://dspy.ai/tutorials/gepa_ai_program/) for both building and improving prompts as well as using its agent framework. I read a paper on prompting about 2 months ago (that I cannot for the life of me find) that showed DSPY prompt improvers beating the best prompt engineering efforts. I have a Deep Research running right now to see if I can find that (AAnd I found it) ... anyway, I am wondering if prompt engineering (as we know it) is dead if we can algorithmically tune prompts that beat Reinforcement Learning, which lead me to the GEPA paper.
2. You could use GEPA as a tool in an agent to improve its interaction with the LLM.
3. I want to explore using DSPY agent framework and how you could combine GEPA capabilities
4. Given GEPA beats Reinforcement learning, specifically GRPO (Group Relative Policy Optimization) techniques... I think GEPA could be used for deep summarization approaches to managing context for agents.
5. A convergence of these ideas in the above papers, blogs and videos also presents a possible path to improving Agentic Search capabilities for large code bases. The problem to be solved here is giving the model a complete view of a brown field code base and helping it navigate it as well as build context for the task you want to accomplish.
6. If this idea works, then GEPA could be used for planning major rewrites and larger tasks... specifically the experiments articulated in the paper regarding `inference time search` In the paper the articulate injection of major documentation like CUDA for a pytorch rewrite (heavy lifting context here) that showed promising results but its literally only one page in the paper... *shows the high value of scowering papers for these kinds of gems* (I've pushed these ideas out a little further below)
7. Agentic search is better that RAG or context stuffing... if it has the right index with descriptions. This has been demonstrated with Claude Code vs Windsurf. Claude Code uses agentic search and the model figures out the dependencies in each file and then searches those dependencies vs vectorizing the code base and using RAG which is the Windsurf approach. This lead me to dig into how ripgrep works...
8. My next idea was to see if memory mapping would help because you don't just have a context window problem (CC only allows 257 megabytes to be loaded directly) in the agent and the LLM itself (Gemini and Grok having the largest context windows)... you also have a memory / RAM problem with loading the file for search. Reading the ripgrep implementation post was an eye opener to the challenges of file search. tldr; ripgrep doesn't use memory mapping! However memory mapping, in a **large file** case beats the ripgrep approach.
9. My idea here is that you could  easily build a ripgrep-like tool for large files (that were memory mapped) in something like Golang. So I've worked out a baseline implementation of a CLI tool that combines the entire codebase into a xml structure that provides the filepath, the filename and the description of the code. My idea is to use GEPA to get the right summarization of the code in question. This would then provide a **high grade** index for an Agent to use a ripgrep style tool to search the file. The challenge here is you have to implement the regex and search algo's in Golang to replicate ripgrep... and then give the agent that tool along with the memory mapped file/s... but if you did that then Claude Code (or any coding agent) should be able to build the context for major feature engineering in large brown field code bases.
10. You could also use these approaches to commandeer large sets of documentation and inject those using GEPA. This `GEPA powered tool` could be then exposed as a tool for the coding agent to use. 
11. Minor idea: All of this led me to typing documents like this out into markdown so I could feed Opus 4 or GPT 5 all the links and my ideas and guide it into following only the links I've given it and provide some possible approaches to the ideas I've outlined. 
12. In addition I built a simple Youtube reader using this API in Gemini: [youtube url api](https://ai.google.dev/gemini-api/docs/video-understanding#youtube)
13. I plan to use this extensively to improve my speed of groking information from youtube interviews and combining them with papers/links.

### Some ideas on how to process large code bases
- Agentic search and the models ability to understand the project structure is the better direction over RAG or other types of indexing.
- Build large single file structures in xml that provide the model what it needs to perform agentic search across the project and build its own context based on a prompt
- The xml file should contain the entire project directory structure to include its dependencies and detailed summary of the file. Use LLM and tuned GEPA prompt to extract the best possible summary of the code in the file. 
- Create a single source.md file that has the entire source tree with xml tags describing every artifact.
- Create modular source.md files that live in a specific module of the code base.
- Memory map all source.md files and enable ripgrep style search across these files to build context.

I was interested in whether memory mapping would provide better performance for file exposure to the model. 
So I dug into `ripgrep` and its design. You can read that here:

[ripgrep design and approach for small files](https://burntsushi.net/ripgrep/)

The tldr; for memory mapping is that it doesn't perform well for many small files so the author of ripgrep eschews that approach for fast directory and file path filtering that uses recursive directory iteration. 

However... if you have large files (e.g. large code base with large modules merged into sizeable source.md files) then memory mapping can be a major performance improvement.

The module level source.md should contain a single description of what that module doesacross all files and specify its given intent and function... as well as including the rollup of the entire source tree within that directory.

## Ideas from papers and videos

In the following paper, specifically in pages 11-12, there is an idea for use of GEPA approaches for inference time search, where they use the feedback function to *dynamically inject domain specific knowledge into the optimization process*. In that case they use specific kernel development expertise (CUDA) normally located in manuals as a search space for errors received in the process of code generation. 

[GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning](https://arxiv.org/pdf/2507.19457)

### Agentic search and local/vertical MCP servers per project
In the following [video](https://www.youtube.com/watch?v=_IlTcWciEC4), Lance Martin (works at LangGraph) mentions that agentic search outperforms RAG/vector-store search and context stuffing approaches by providing a simple llms.txt file with the links and an LLM generated description of the content of that link. 

The specific place in the video he explains this is here:
[llms.txt vs RAG vs context-stuffing](https://youtu.be/_IlTcWciEC4?t=1116)

He has a python project that creates llms.txt from documentation/website here:
[llms.txt generator in python](https://github.com/rlancemartin/llmstxt_architect/tree/main)

What he found in his simple test case was that the llms.txt approach outperformed the other two approaches by 20%. In addition in a test of Claude Code <> Cursor Claude Code outperformed by 15% on the llms.txt agentic search. 

**tldr;** -> If you give a good agent (CC in this case) good file search tools and an llms.txt file to help it understand the contents of the documents (so that the LLM/agent knows what is in each file) it can outperform other methods. 

**Important:** timing of this test was April 2025 (things can change quickly)



In addition another good idea in this video was use of `specific to project` mcp servers... effectively purpose built for only the project you're working on. So for example you may be working on a project that uses the Youtube API and you want an llms.txt exposed via MCP you could have just that MCP server exposing that for the repo you are in.


[Link to ideas about compression and search from Manus](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus#:~:text=Our%20compression%20strategies,Turing%20Machines.)

The above is a very interesting idea related to restoring context and using compression to do so with experiencing context loss.

Context offloading to disk and keeping the problems and mistakes in the context are important ideas explored in the [Manus agent building lessons](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)

Another good article is Drew Bruenig on [How Long Contexts Fail](https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html). Important reading on understanding why pure `context stuffing` can be problematic.
