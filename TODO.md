To do list

 - [x] Ensure single task is working using `qwen3-4b`, both for `futurex-online` and `futurex-past`
    - `qwen3-4b` is not actually available on OpenRouter, other than a free rate-limited version. For now we'll use `qwen3-30b-a3b`. 
    - If we decide to post-train `qwen3-4b` first, we'll need to run the eval locally rather than using Openrouter
    - Note: `qwen-30b-a3b` when tested on `futurex-online` task 1: responded with
        ```
        Final Answer Summary**  \nThe task to predict the outcome of the match between **Stade Rennais FC 1901** and **Racing Club de Lens** on **2025-09-28** could not be completed due to insufficient data and tool limitations.
        ```
 - [x] Add `just commands` for testing 1 task, testing 10 tasks, and testing all tasks for a particular benchmark, including which model to use
 - [x] Run eval on 10 samples from `futurex-past` for `qwen3-30b-a3b` and with `tongyi-deepresearch-30b-a3b`
    - Note: Scores 5/10, the model is consistently picking 'A'
    - Appears only 'reading' tool is being used
    - Current setting seems to be with a single worker agent
 - [x] Add cost tracking and test on single sample
 - [ ] Add better summary of number of tool calls, number of sub agents etc
 - [x] See if we can speed things up. Enable `Throughput (highest first)` provider sort in OpenRouter
 - [ ] Establish which configs will lead to improved performance
    - Which tool calls do we need for `futurex`?
 - [ ] Visualise results in an evals notebook