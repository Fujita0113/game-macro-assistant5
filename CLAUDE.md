# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GameMacroAssistant is a desktop automation tool for PC games that allows users to record, edit, and replay mouse/keyboard operations. The tool uses visual recognition to match screen conditions before executing actions.

## Core Architecture

Based on the requirements document, this application should implement:

### Recording System
- Global input capture for mouse and keyboard operations
- Screen capture with native resolution support and GDI fallback
- ESC key termination for recording sessions
- Error handling for capture failures (logs `Err-CAP` codes)

### Visual Editor
- Block-based macro representation with drag-and-drop reordering
- Image editing for condition screenshots (double-click to edit, rectangular selection)
- Undo/redo support (Ctrl+Z)

### Execution Engine  
- Global hotkey triggering (e.g., Ctrl+Shift+F10)
- Image matching for conditional execution
- Timeout handling with notification system (logs `Err-TMO` codes)
- Progress indication in system tray

### File Management
- Encrypted `.gma.json` file format with password protection (8+ characters)
- Three-attempt password validation with error feedback

## Key Technical Requirements

- **Screen Capture**: Must handle fullscreen games with fallback to GDI when native capture fails
- **Visual Recognition**: Image matching between stored conditions and current screen state
- **Global Hooks**: System-wide input capture and hotkey registration
- **Encryption**: Secure storage of macro files with password protection
- **Error Logging**: Comprehensive logging with specific error codes (Err-CAP, Err-TMO)
- **UI Framework**: Visual editor supporting drag-and-drop, image editing, and block manipulation

## Development Notes

- The project currently contains only requirements documentation
- Implementation should focus on defensive automation (game assistance) rather than exploitative automation
- Error handling and user feedback are critical given the real-time nature of game automation
- Consider cross-platform compatibility for screen capture methods

## Development Principles

すべての開発において、以下の原則を厳守してください：

- **KISS (Keep It Simple, Stupid)**: 複雑な抽象化を避け、必要十分な機能のみ実装すること
- **YAGNI (You Aren’t Gonna Need It)**: 現在必要な機能のみに集中し、不要な未来機能は実装しないこと
- **Incremental**: 動作する最小限の機能から段階的に拡張していくこと
- **TDD (Test-Driven Development)**: Claude が書いたコードの信頼性を担保するため、必ずテストを書いてから開発を進めること


### Claude Code Constraints

- **IMPORTANT**: Claude Code cannot change directories during a session. DO NOT use `cd` commands as they will cause errors
- All file operations must use absolute paths from the current working directory
- When working in worktrees, start Claude Code session from within the worktree directory itself
- Use tools like `Bash` for operations that require specific directory context, but avoid changing the working directory

## Worktree Management

When creating worktrees for feature development:

1. **Create branch first:** Always create a new branch before adding worktree
   ```bash
   git checkout -b feat/feature-name
   git checkout main  # return to main branch
   ```

2. **Add worktree:** Then add the worktree pointing to the created branch
   ```bash
   git worktree add worktrees/feat-feature-name feat/feature-name
   ```

3. **Work in worktree:** Navigate to the worktree directory for development
   ```bash
   cd worktrees/feat-feature-name
   ```
   **Note:** Start your Claude Code session from within the worktree directory, as Claude Code cannot change directories during execution.

4. **Commit and push changes:** ALWAYS commit and push any implementation changes
   ```bash
   git add .
   git commit -m "Descriptive commit message"
   git push origin feat/feature-name
   ```

This approach ensures proper branch tracking and avoids reference errors during worktree creation.

## Issue Completion Workflow

When a user reports that implementation is completed, follow this standardized workflow:

1. **Verify and Close Issue:** Check issue status and close with completion comment
   ```bash
   gh issue view {issue_number} --json state,title
   gh issue close {issue_number} --comment "Implementation completed. All acceptance criteria have been met."
   ```

2. **Merge Feature Branch:** Merge the completed feature branch to main
   ```bash
   git merge feat/feature-name
   ```

3. **Update Epic Tracking Issue:** Update progress in the parent Epic issue
   ```bash
   gh issue edit {epic_issue_number} --body "$(cat <<'EOF'
   [Updated Epic content with current progress, marking completed items with [x]]
   EOF
   )"
   ```

4. **Clean Up Worktree:** Remove worktree and delete merged branch
   ```bash
   git worktree remove worktrees/feat-feature-name
   git branch -d feat/feature-name
   git worktree list  # verify cleanup
   ```

5. **Verify Final State:** Confirm all cleanup completed successfully
   ```bash
   git log --oneline -3  # check merge commit
   gh issue view {epic_issue_number}  # verify Epic update
   ```

This workflow ensures consistent project management and maintains clean repository state.

## Bug Fix Workflow

バグ修正の際は、以下のフローを厳守してください：

1. **ロギングで原因を完全に特定**
   - 詳細なログ出力を追加してバグの根本原因を特定
   - デバッグ情報を使って問題の再現手順を明確化

2. **回帰テストを作成して、通らないのを確認**
   - バグを再現するテストケースを作成
   - テストが失敗することを確認（Red状態）

3. **TDDで修正**
   - テストを通すための最小限の修正を実装
   - 他の機能に影響を与えないよう注意深く修正

4. **回帰テストが通るのを確認**
   - 作成したテストケースが成功することを確認（Green状態）
   - 既存のすべてのテストも引き続き成功することを確認

このフローにより、バグの確実な修正と将来の回帰防止を保証します。

## Troubleshooting

For technical issues and error resolution, see documentation in `docs/troubleshooting/`.

## Definition of Done

あるタスクが完了したと見なされるのは、以下の条件がすべて満たされた場合のみです。

- **全てのテストが成功すること** (例: `pytest`)
- **Ruffのリンターとフォーマッターがエラーなくパスすること** (例: `ruff check .` および `ruff format . --check`)
- Git にすべての変更がコミットされ、リモートにプッシュされていること

これらのコマンドは、すべて終了コード0で完了しなければなりません。コマンド実行中の表示（ドットなど）ではなく、最終的な終了コードのみが成功の証拠となります。

## Worktree Synchronization Issues

If an agent reports that previous implementations are not visible in their worktree:

1. **Check worktree status:** The worktree may be based on an outdated commit
   ```bash
   # Navigate to worktree directory before starting Claude Code session
   cd worktrees/feat-feature-name
   # Then in Claude Code session (which cannot use cd):
   git log --oneline -5  # Compare with main branch commits
   ```

2. **Update worktree with latest main:** Merge latest changes from main branch
   ```bash
   # Navigate to worktree directory before starting Claude Code session
   cd worktrees/feat-feature-name
   # Then in Claude Code session (which cannot use cd):
   git add . && git commit -m "WIP: Save current work"  # Save any uncommitted changes
   git merge main  # This may cause merge conflicts
   ```

3. **Resolve merge conflicts if needed:** Handle conflicts in shared files like requirements.txt or main.py
   ```bash
   git status  # See conflicted files
   # Manually resolve conflicts in each file
   git add resolved-file.txt
   git commit -m "Resolve merge conflicts with main branch"
   ```

4. **Verify integration:** Ensure previous implementations are now visible
   ```bash
   git log --oneline -10  # Should show merged commits from other features
   ```

**Important:** Any worktree that was created before other features were merged will need this synchronization step to access the latest implementations.