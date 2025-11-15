# OpenCode + Neo-Clone Enhanced System 🎯

**Your Complete AI Coding Assistant with 100% Free Models**

This release contains your complete OpenCode + Neo-Clone system with **36+ free AI models**, **12 enhanced skills**, and **100% MiniMax replication** achieved.

---

## 🚀 **Quick Start**

### **Prerequisites**
- **Bun** (for OpenCode)
- **Python 3.8+** (for Neo-Clone)

### **Installation**
1. **Extract & Install:**
   ```bash
   cd opencode && bun install
   cd neo-clone && pip install -r requirements.txt
   ```

2. **Configure Free Models:**
   ```bash
   cd ..
   opencode config set model "opencode/big-pickle"
   ```

3. **Launch Your System:**
   ```bash
   # Terminal 1: OpenCode Server
   bun dev
   
   # Terminal 2: Enhanced Neo-Clone TUI
   cd neo-clone && python main.py --enhanced
   ```

**That's it!** Your complete AI coding assistant is running with 100% free models.

### **📋 See Also**
- **Detailed Installation**: `INSTALLATION_GUIDE.md`
- **Update Instructions**: `CLINES_UPDATE_TASK.md`
- **System Verification**: Run `python detailed_verification.py`

### Contributing

opencode is an opinionated tool so any fundamental feature needs to go through a
design process with the core team.

> [!IMPORTANT]
> We do not accept PRs for core features.

However we still merge a ton of PRs - you can contribute:

- Bug fixes
- Improvements to LLM performance
- Support for new providers
- Fixes for env specific quirks
- Missing standard behavior
- Documentation

Take a look at the git history to see what kind of PRs we end up merging.

> [!NOTE]
> If you do not follow the above guidelines we might close your PR.

To run opencode locally you need.

- Bun
- Golang 1.24.x

And run.

```bash
$ bun install
$ bun dev
```

#### Development Notes

**API Client**: After making changes to the TypeScript API endpoints in `packages/opencode/src/server/server.ts`, you will need the opencode team to generate a new stainless sdk for the clients.

### FAQ

#### How is this different than Claude Code?

It's very similar to Claude Code in terms of capability. Here are the key differences:

- 100% open source
- Not coupled to any provider. Although Anthropic is recommended, opencode can be used with OpenAI, Google or even local models. As models evolve the gaps between them will close and pricing will drop so being provider-agnostic is important.
- A focus on TUI. opencode is built by neovim users and the creators of [terminal.shop](https://terminal.shop); we are going to push the limits of what's possible in the terminal.
- A client/server architecture. This for example can allow opencode to run on your computer, while you can drive it remotely from a mobile app. Meaning that the TUI frontend is just one of the possible clients.

#### What's the other repo?

The other confusingly named repo has no relation to this one. You can [read the story behind it here](https://x.com/thdxr/status/1933561254481666466).

---

**Join our community** [Discord](https://discord.gg/opencode) | [X.com](https://x.com/opencode)
