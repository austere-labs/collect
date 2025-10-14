## Notes on DSPy and GEPA Prompting

Resources/Readings: 
- [Drew Breunig's talk on DSPy](https://www.youtube.com/watch?v=zWXPxDMiJCY)  
- [Drew Breunig's blog post on DSPy](https://www.dbreunig.com/2025/06/10/let-the-model-write-the-prompt.html)
- [Overture Maps Data](https://overturemaps.org/download/)

From OpenAI's GPT-4.1 Prompting Guide:
- The Task - 1%
- Chain of Thought Instructions - 19%
- Detailed Context & Instructions - 39%
- Tool Definitions - 5%
- Formatting Instructions - 32%
- Other - 4%

### This is the visual for the above:
[Link to A Prompt Example: SWE Bench](https://www.dbreunig.com/img/dais/dais_2025_dbreunig_007.jpg)

tldr; Prompt structure and order matters and there are specific repeatable patterns.

Compound AI definition:
> A compound AI pipeline, or compound AI system, is a modular workflow that combines multiple specialized AI models, retrieval systems, and other tools to solve complex tasks more effectively than a single, monolithic model. Instead of relying on one large model to handle all aspects of a task, this approach orchestrates several components, each optimized for a specific part of the process. 

Idea: Transaction Enrichment and Merchant identification in financial data ->
- Use Overture's data (point of interest) to match Merchant data
- Use large hand labeled data sets of transactions < - > POI < - > Merchant
- Use DSPy to train a model to match transactions to POI's and Merchant's
- Use GEPA to improve the model
- Use the model to match transactions to POI's and Merchant's

***

The following [post](https://x.com/AsfiShaheen/status/1967866903331999807) was a great x thread on how to use GEPA:
- Hand labeled data set thats accurate
- Text explanation for WHY its accurate (this is the **interesting** bit). The explanation is not specifically required in GEPA.
- From GEPA docs: "In addition to scalar scores returned by the metrics, users can also provide GEPA with a **text feedback to guide the optimization process**. Such textual feedback provdes GEPA more visibility into why the system got the score that it did, and then GEPA can intropsect to indentify how to improve the score."
- Use Opus or Gemini 2.5 Pro to get the labeling data to 90% and then hand check the results and tune them.
- Then use the 300+ golden data set and feed the rest into dspy.GEPA BUT use a faster and cheaper model to process the documents, like Gemini 2.5 Lite.

> [@AsfiShaheen](https://x.com/AsfiShaheen) is basically building a system that tags and labels every page of a pdf, in his case these pdfs are financial reports from Pakistan companies that are publicly traded. He uses Opus and Gemini 2.5 Pro with a high token budget to create his data set and then he manually checks the results, freezes them and they become his golden data set. He also provides a screen shot of his data set [here](https://x.com/AsfiShaheen/status/1968059188418056326)


Further Exploration and Reading: TODO -> 
> This is a thread from one of the replies here: [from Lakshya A Agrawal](https://x.com/LakshyAAAgrawal/status/1968236513810087975) where he provides a [link to a jupyter notebook](https://github.com/gepa-ai/gepa/blob/main/src/gepa/examples/dspy_full_program_evolution/arc_agi.ipynb) where GEPA actually discovers an sophisticated agent. 

Papers to read:
- [Less is More: Recursive Reasoning with Tiny Networks](https://arxiv.org/pdf/2510.04871)
- [Code base for the paper above ^^](https://github.com/SamsungSAILMontreal/TinyRecursiveModels)