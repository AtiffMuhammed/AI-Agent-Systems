# A useful launch, with verifiable evidence

The specific audience is student makers and solo builders whose project knowledge is scattered across notes, READMEs, and test plans. Lead with the job this tool does: find a decision, verify its source, and carry forward the next step.

## One-minute demonstration

1. Start `python -m agent_workspace serve` and load the sample. Explain that the sample notes are fictional.
2. Ask how often the firmware samples soil moisture. Open the result's source reference and show the 30-second interval in its original lines.
3. Ask about calibration tests. Add a TODO to the board, move it to In progress, and reload to show persistence.
4. Download a Markdown report and open the evidence snapshot. If demonstrating AI synthesis, use a real configured provider and show its actual mode label.

Record the real application. Do not replace it with a generated screenshot or a scripted mock conversation.

## Before wider promotion

Have three builders import a small set of their own shareable notes. Ask them to find a decision, identify an unanswered question, and save a next step. Record the setup failures, confusing results, and unsupported file formats. Fix the repeated problems first.

Suggested repository topics, once publishing access is available: `python`, `local-first`, `rag`, `ollama`, `project-management`, `sqlite`, `developer-tools`.

The README has a quick start, a specific use case, a working offline sample, clear limitations, and a contribution path. Add a real screen recording and release notes after you complete the unverified checks in `REVIEW.md`. Share it only in communities where this solves a relevant problem, ask for feedback, and keep the star request optional. There is no guaranteed star count.

## Research behind these choices

- [GitHub's README guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes) supports explaining the project, setup, and contribution path. It does not promise stars.
- [Ollama chat API](https://docs.ollama.com/api/chat) and [structured outputs](https://docs.ollama.com/capabilities/structured-outputs) informed the local model adapter and response shape.
- [OpenRouter API reference](https://openrouter.ai/docs/api_reference/overview) informed request/response handling and JSON mode.
- [Stardance's public site](https://stardance.hackclub.com/) describes publishing open-source projects and peer feedback. Its public landing page does not settle this project's reuse eligibility. Disclose the existing repository and ask organizers about the current submission rules.

A project-specific recommendation: use the same repository's actual new diffs as evidence for V3, and clearly distinguish them from the earlier V1/V2 work.
