To do list

 - [x] Ensure single task is working using `qwen3-4b`, both for `futurex-online` and `futurex-past`
    - `qwen3-4b` is not actually available on OpenRouter, other than a free rate-limited version. For now we'll use `qwen3-30b-a3b`. 
    - If we decide to post-train `qwen3-4b` first, we'll need to run the eval locally rather than using Openrouter
    - Note: `qwen-30b-a3b` when tested on `futurex-online` task 1 was breaking because the tools it was connecting to were failing.
 - [x] Add `just` commands for testing 1 task, 10, 50 tasks, and testing all tasks for a particular benchmark, including which model to use
 - [x] Run eval on 10 samples from `futurex-past` for `qwen3-30b-a3b` and with `tongyi-deepresearch-30b-a3b`
    - Note: Scores 5/10, the model is consistently picking 'A'
    - Appears only 'reading' tool is being used
    - Current setting seems to be with a single worker agent
    - After visualising the tool calls, can see they are failing
 - [x] Add a way to simply see the main sub-agents and their success state from the log file
 - [x] Add cost tracking and test on single sample
 - [x] Add better summary of number of tool calls, number of sub agents etc
 - [x] See if we can speed things up. Enable `Throughput (highest first)` provider sort in OpenRouter
 - [x] Add a CLAUDE.md to serve as statefulness across Claude code sessions.
 - [x] Get Search MCP tool use working (Serper)
 - [x] Add a level filter
 - [ ] Run on 10 level 4 tasks and check that 
 - [ ] Fix eval for all question types.
 - [ ] Establish which configs will lead to improved performance
    - Which tool calls do we need for `futurex`?
 - [ ] Visualise results in an evals notebook


Open questions list
 - [ ] Which tool calls were actually used with GPT-5 to get the SOTA result?
 - [x] I'm getting rate-limited a lot in OpenRouter for `alibaba/tongyi-deepresearch-30b-a3b`. Not sure why
    - This is because they only have 1 provider - `AtlasCloud` which is shitting itself.
 - [ ] Which exact configuration was used for the gpt-5 benchmark?
 - [ ] What needs to be done to properly reproduce the number on the `FutureX` website?
    - The overall score is 10%, 20%, 30% and 40% weighted average over the 4 difficulty tiers of questions.
 - [ ] Which tools make sense to use?
    - From FutureX paper: "Another benchmark, GAIA [18], focuses on general-purpose assistant capabilities with 466 real-world questions that require reasoning, multi-modality, web search, and tool use."
    - Shall we just use the same tools as the GAIA benchmark?
 - [ ] Any way to actually make this significantly faster? Still currently taking minutes for every question, prohibitively slow to test anything at the dataset level.