<div align="center">
  <img src="docs/mkdocs/docs/assets/miroflow_logo.png" width="100%" alt="MiroFlow" />
</div>

<br> 

<div align="center">

[![DOCS](https://img.shields.io/badge/Documentation-4285F4?style=for-the-badge&logo=gitbook&logoColor=white)](https://miromindai.github.io/MiroFlow/)
[![DEMO](https://img.shields.io/badge/Demo-FFB300?style=for-the-badge&logo=airplayvideo&logoColor=white)](https://dr.miromind.ai/)
[![MODELS](https://img.shields.io/badge/Models-5EDDD2?style=for-the-badge&logo=huggingface&logoColor=ffffff&labelColor)](https://huggingface.co/collections/miromind-ai/mirothinker-v02-68af084a18035f57b17cd902)
[![DATA](https://img.shields.io/badge/Data-0040A1?style=for-the-badge&logo=huggingface&logoColor=ffffff&labelColor)](https://huggingface.co/datasets/miromind-ai/MiroVerse-v0.1)

[![GITHUB](https://img.shields.io/badge/Github-24292F?style=for-the-badge&logo=github&logoColor=white)](https://github.com/MiroMindAI)
[![WEBSITE](https://img.shields.io/badge/Website-4285F4?style=for-the-badge&logo=google-chrome&logoColor=white)](https://miromind.ai/)
[![DISCORD](https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.com/invite/GPqEnkzQZd)
[![WeChat](https://img.shields.io/badge/WeChat-07C160?style=for-the-badge&logo=wechat&logoColor=white)](https://huggingface.co/datasets/miromind-ai/MiroFlow-Benchmarks/resolve/main/assets/wechat.png)
[![RedNote](https://img.shields.io/badge/RedNote-FF2442?style=for-the-badge&logo=revoltdotchat&logoColor=white)](https://www.xiaohongshu.com/user/profile/5e353bd80000000001000239)

</div>

<div align="center">

### 🚀 [Try our Demo!](https://dr.miromind.ai/) | 📚 [Full Documentation](https://miromindai.github.io/MiroFlow/)｜[中文](README_zh.md)｜[日本語](README_ja.md)

</div>

<table align="center" style="border: 1px solid #ccc; border-radius: 8px; padding: 12px; background-color: #f9f9f9; width: 60%;">
  <tr>
    <td style="text-align: center; padding: 10px;">
      <strong>Research Assistant Demo</strong> - 
      <span style="font-size: 0.9em; color: #555;">Read CVPR 2025 Best Paper and Provide Research Advice</span>
      <br>
      <video src="https://github.com/user-attachments/assets/99ed3172-6e9a-467a-9ccb-be45957fe2e4"
             controls muted preload="metadata"
             width="50%" height="50%"
      </video>
    </td>
  </tr>
</table>


## 📋 Table of Contents

- [📰 News & Updates](#-news--updates)
- [🤖 What is MiroFlow?](#-what-is-miroflow)
- [✨ Performance on Benchmarks](#-performance-on-benchmarks)
- [🚀 Get Started in Under 5 Minutes](#-get-started-in-under-5-minutes)
- [🤖 MiroFlow Framework](#-miroflow-ai-agentic-foundation-framework)
- [🤝 Contributing](#-contributing)
- [❓ FAQ](#-faq)
- [📄 License & Support](#-license--support)
- [👥 Acknowledgments](#-acknowledgments-and-contributors)


## 📰 News & Updates

- **[2025-09-15]**: 🎉🎉 **MiroFlow v0.3** - Enhanced codebase architecture and significantly improved benchmark performance. MiroFlow now ranks #1 in the future prediction benchmark.
- **[2025-08-27]**: **MiroFlow v0.2** - Achieves state-of-the-art performance across [multiple agentic benchmarks](https://miromind.ai/blog/miroflow), including HLE (27.2%), HLE-Text-Only (29.5%), BrowserComp-EN (33.2%), BrowserComp-ZH (47.1%), and xBench-DeepSearch (72.0%)
- **[2025-08-26]**: Released [GAIA Validation Trace](docs/public_trace.md) (73.94% pass@1) and [Gradio Demo](https://github.com/MiroMindAI/MiroThinker/tree/main/apps/gradio-demo) for local deployment
- **[2025-08-08]**: 🎉 **MiroFlow v0.1** - Complete open-source release of framework, models, and training data

---

## 🤖 What is MiroFlow?

**MiroFlow** is a comprehensive framework for building intelligent AI agents that achieve state-of-the-art performance on complex reasoning tasks. It provides enhanced conversation management, flexible tool integration, and extensive benchmark evaluations across multiple datasets. 

**MiroThinker** is the open-source agentic model series built on this framework.

### 🌟 Key Highlights

- 🏆 **State-of-the-Art Performance**: #1 ranking across [multiple agentic benchmarks](https://miromindai.github.io/MiroFlow/evaluation_overview/)
- 📊 **Premium Training Data**: Curated datasets via [MiroVerse](https://huggingface.co/datasets/miromind-ai/MiroVerse-v0.1)
- 🤖 **Open Models**: Complete collection at [MiroThinker](https://huggingface.co/collections/miromind-ai/mirothinker-v01-689301b6d0563321862d44a1)
- 🔧 **Full Training Stack**: SFT/DPO recipes at [MiroTrain](https://github.com/MiroMindAI/MiroTrain)
- 🎯 **Advanced RL**: Reinforcement learning via [MiroRL](https://github.com/MiroMindAI/MiroRL)


### ✨ Performance on Benchmarks

<img width="100%" alt="image" src="docs/mkdocs/docs/assets/futurex-09-12.png" />

We achieved the #1 ranking on the FutureX Benchmark Leaderboard as of September 10, 2025.

<div align="center">
  <img src="docs/mkdocs/docs/assets/miroflow-0.2-performance_short.png" width="90%" alt="Comprehensive Benchmark Performance Comparison" style="border-radius: 8px; box-shadow: 0 4px 8px rgba(3, 3, 3, 0.1);">
</div>

We benchmark MiroFlow on a series of benchmarks including **GAIA**, **HLE**, **BrowseComp** and **xBench-DeepSearch** and achieved SOTA results.

| Model/Framework | GAIA Val | HLE | HLE-Text | BrowserComp-EN | BrowserComp-ZH | xBench-DeepSearch |
|----------------|----------|-----|----------|----------------|----------------|-------------------|
| **MiroFlow** | **82.4%** | **27.2%** | 29.5% | 33.2% | **47.1%** | **72.0%** |
| OpenAI Deep Research | 67.4% | 26.6% | - | **51.5%** | 42.9% | - |
| Gemini Deep Research | - | 26.9% | - | - | - | 50+% |
| Kimi Researcher | - | - | 26.9% | - | - | 69.0% |
| WebSailor-72B | 55.4% | - | - | - | 30.1% | 55.0% |
| Manus | 73.3% | - | - | - | - | - |
| DeepSeek v3.1 | - | - | **29.8%** | - | - | 71.2% |


# 🚀 Get Started in Under 5 Minutes

Clone the repository, configure your API key, and run your first intelligent agent. You'll just need one `OPENROUTER_API_KEY`.

## 📋 Prerequisites

- **Python**: 3.12 or higher
- **Package Manager**: [`uv`](https://docs.astral.sh/uv/)
- **Operating System**: Linux, macOS

## ⚡ Quick Setup

**Example**: Intelligent document analysis with file processing capabilities.

```bash
# 1. Clone and setup
git clone https://github.com/MiroMindAI/MiroFlow && cd MiroFlow
uv sync

# 2. Configure API key
cp .env.template .env
# Edit .env and add your OPENROUTER_API_KEY

# 3. Run your first agent
uv run main.py trace --config_file_name=agent_quickstart_1 --task="What is the first country listed in the XLSX file that have names starting with Co?" --task_file_name="data/FSI-2023-DOWNLOAD.xlsx"
```

🎉 **Expected Output:** Your agent should return **\boxed{Congo Democratic Republic}** 😊

> **💡 Tip:** If you encounter issues, check that your API key is correctly set in the `.env` file and that all dependencies are installed.

**🎯 Comprehensive Benchmark Suite**:
- **GAIA Validation**: A benchmark for General AI Assistants. ([paper](https://arxiv.org/abs/2311.12983))
- **GAIA-Text-103**: A subset of GAIA Validation for text-only tasks. ([paper](https://arxiv.org/abs/2505.22648))
- **HLE**: Humanity's Last Exam. ([paper](https://arxiv.org/abs/2501.14249))
- **HLE-Text-500**: A subset of HLE for text-only tasks. ([paper](https://arxiv.org/pdf/2504.21776))

Follow our detailed guides to reproduce benchmark results in our [Benchmarks Documentation](https://miromindai.github.io/MiroFlow/evaluation_overview/)

# 🤖 MiroFlow: AI Agentic Foundation Framework

MiroFlow is a high-performance, modular framework for building intelligent AI agents that deliver state-of-the-art results on complex reasoning tasks. The framework features advanced multi-turn conversation capabilities, extensive tool ecosystem integration, and hierarchical sub-agent orchestration for optimal task completion. Learn more about our agent [workflow architecture](https://miromindai.github.io/MiroFlow/core_concepts/).

<div align="center">
<img src="docs/mkdocs/docs/assets/miroflow_architecture.png" width="100%" alt="MiroFlow Architecture">
</div>

## 🤝 Contributing

We welcome contributions from the community! Whether you're fixing bugs, adding features, or improving documentation, your help is appreciated.

- 📋 **Issues**: Report bugs or request features via [GitHub Issues](https://github.com/MiroMindAI/MiroFlow/issues)
- 🔀 **Pull Requests**: Submit improvements via pull requests
- 💬 **Discussions**: Join our [Discord community](https://discord.com/invite/GPqEnkzQZd) for questions and discussions

## ❓ FAQ

<details>
<summary><strong>What API keys do I need?</strong></summary>
<br>
You only need an OpenRouter API key to get started. OpenRouter provides access to multiple language models through a single API.
</details>

<details>
<summary><strong>Can I use other language models besides OpenRouter?</strong></summary>
<br>
Yes, MiroFlow supports various language models. Check our documentation for configuration details.
</details>

<details>
<summary><strong>How do I capture console logs from a run?</strong></summary>
<br>
All commands executed through `main.py` now mirror console output to timestamped files under `logs/`.
Set `LOGGER_DIR` in your environment (or `.env`) to change the folder, or `LOGGER_FILE` to point to an exact file path.
</details>

<details>
<summary><strong>How do I reproduce the benchmark results?</strong></summary>
<br>
Follow our detailed <a href="https://miromindai.github.io/MiroFlow/evaluation_overview/">Benchmarks Documentation</a> for step-by-step reproduction guides.
</details>

<details>
<summary><strong>Is there commercial support available?</strong></summary>
<br>
For commercial inquiries and enterprise support, please contact us through our <a href="https://miromind.ai/">website</a>.
</details>

## 📄 License & Support

This project is licensed under the Apache License 2.0.


<div align="center">
    <img src="https://api.star-history.com/svg?repos=MiroMindAI/MiroFlow&type=Date" alt="Star History Chart" height="300">
</div>

### References

Technical report is coming soon!

```
@misc{2025mirothinker,
    title={MiroFlow: An Open-Source Agentic Framework for Deep Research},
    author={MiroMind AI Team},
    howpublished={\url{https://github.com/MiroMindAI/MiroFlow}},
    year={2025}
}
```



## 👥 Acknowledgments and Contributors

- **Benchmark Contributors** for the comprehensive evaluation datasets
- **Open Source Community** for the tools and libraries that make this possible

We thank all contributors who have helped make MiroFlow better:

<a href="https://github.com/MiroMindAI/MiroFlow/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=MiroMindAI/MiroFlow" />
</a>

Join our community and help us build the future of AI agents!
