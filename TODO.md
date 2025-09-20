To do list

 - [x] Ensure single task is working using `qwen3-4b`, both for `futurex-online` and `futurex-past`
    - `qwen3-4b` is not actually available on OpenRouter, other than a free rate-limited version. For now we'll use `qwen3-30b-a3b`. 
    - If we decide to post-train `qwen3-4b` first, we'll need to run the eval locally rather than using Openrouter
    - Note: `qwen-30b-a3b` when tested on `futurex-online` task 1: responded with
        ```
        Final Answer Summary**  \nThe task to predict the outcome of the match between **Stade Rennais FC 1901** and **Racing Club de Lens** on **2025-09-28** could not be completed due to insufficient data and tool limitations.
        ```
 - [x] Add `just commands` for testing 1 task, testing 10 tasks, and testing all tasks for a particular benchmark, including which model to use
 - [ ] Find appropropriate models which will also 