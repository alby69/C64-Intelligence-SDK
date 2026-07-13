#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess
import configparser

def run_cmd(args, cwd=None, capture_output=True, check=True):
    """Utility function to run a system command using subprocess."""
    try:
        res = subprocess.run(args, cwd=cwd, text=True, capture_output=capture_output, check=check)
        return res.stdout.strip() if capture_output else ""
    except subprocess.CalledProcessError as e:
        if capture_output:
            cmd_str = " ".join(args)
            err_msg = e.stderr.strip() if e.stderr else e.stdout.strip() if e.stdout else str(e)
            print(f"Error running command '{cmd_str}' in '{cwd or '.'}': {err_msg}", file=sys.stderr)
        raise e

def load_submodules():
    """Reads .gitmodules and parses submodule details."""
    gitmodules_path = ".gitmodules"
    if not os.path.exists(gitmodules_path):
        print(f"Error: {gitmodules_path} not found in current directory.", file=sys.stderr)
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(gitmodules_path)

    submodules = {}
    for section in config.sections():
        # Section name is typically: submodule "core"
        if section.startswith('submodule "') and section.endswith('"'):
            name = section[11:-1]
            submodules[name] = {
                "name": name,
                "path": config.get(section, "path", fallback=name),
                "url": config.get(section, "url", fallback=""),
                "branch": config.get(section, "branch", fallback="main"),
            }
    return submodules

def is_initialized(path):
    """Checks if a submodule is initialized (has a .git file/folder inside its path)."""
    git_indicator = os.path.join(path, ".git")
    return os.path.exists(path) and os.path.exists(git_indicator)

def is_dirty(path):
    """Checks if a repository has uncommitted changes."""
    if not is_initialized(path):
        return False
    status = run_cmd(["git", "status", "--porcelain"], cwd=path)
    return len(status) > 0

def get_current_branch(path):
    """Gets the current active branch of a repository."""
    if not is_initialized(path):
        return "Not Initialized"
    branch = run_cmd(["git", "branch", "--show-current"], cwd=path)
    if not branch:
        # Check if detached HEAD
        return "(detached HEAD)"
    return branch

def get_current_commit(path):
    """Gets the current short commit hash of a repository."""
    if not is_initialized(path):
        return "N/A"
    return run_cmd(["git", "rev-parse", "--short", "HEAD"], cwd=path)

def check_unpushed_commits(path, branch):
    """Checks if there are unpushed local commits compared to remote."""
    if not is_initialized(path):
        return False
    try:
        # Check if the upstream branch exists
        upstream = f"origin/{branch}"
        out = run_cmd(["git", "rev-list", f"{upstream}..HEAD"], cwd=path)
        return len(out.strip()) > 0
    except Exception:
        # Upstream might not exist or branch might be detached
        return False

def check_unpulled_commits(path, branch):
    """Checks if there are commits on remote not yet pulled."""
    if not is_initialized(path):
        return False
    try:
        upstream = f"origin/{branch}"
        out = run_cmd(["git", "rev-list", f"HEAD..{upstream}"], cwd=path)
        return len(out.strip()) > 0
    except Exception:
        return False

def cmd_status(args):
    """Prints status of all submodules."""
    submodules = load_submodules()
    print("\n=== Submodule Status Report ===")
    print(f"{'Submodule':<15} | {'Path':<12} | {'Branch (Config)':<18} | {'Active Branch':<18} | {'Commit':<10} | {'Status':<25}")
    print("-" * 110)
    for name, sub in submodules.items():
        path = sub["path"]
        config_branch = sub["branch"]

        if not is_initialized(path):
            print(f"{name:<15} | {path:<12} | {config_branch:<18} | {'N/A':<18} | {'N/A':<10} | \033[93mNot Initialized\033[0m")
            continue

        active_branch = get_current_branch(path)
        commit = get_current_commit(path)

        status_parts = []
        if is_dirty(path):
            status_parts.append("\033[91mDirty (uncommitted changes)\033[0m")

        # Check pushes/pulls (best effort, may require fetch first)
        if active_branch != "(detached HEAD)":
            if check_unpushed_commits(path, config_branch):
                status_parts.append("\033[92mUnpushed Commits\033[0m")
            if check_unpulled_commits(path, config_branch):
                status_parts.append("\033[94mRemote Updates Available\033[0m")

        if not status_parts:
            status_parts.append("\033[92mClean & Up-to-date\033[0m")

        status_str = ", ".join(status_parts)
        print(f"{name:<15} | {path:<12} | {config_branch:<18} | {active_branch:<18} | {commit:<10} | {status_str}")
    print("=" * 110 + "\n")

def cmd_update(args):
    """Updates submodules to their configured remote branch, commits pointers in parent."""
    submodules = load_submodules()
    parent_changed = False

    # Check for uncommitted changes in submodules first if not using --force
    if not args.force:
        dirty_subs = [name for name, sub in submodules.items() if is_dirty(sub["path"])]
        if dirty_subs:
            print(f"Error: The following submodules have uncommitted changes: {', '.join(dirty_subs)}.", file=sys.stderr)
            print("Commit, discard, or run with --force to stash changes automatically.", file=sys.stderr)
            sys.exit(1)

    for name, sub in submodules.items():
        path = sub["path"]
        branch = sub["branch"]
        print(f"\n--- Updating '{name}' (path: '{path}', tracking: '{branch}') ---")

        # 1. Initialize if not present
        if not is_initialized(path):
            print(f"Submodule '{name}' is not initialized. Initializing...")
            run_cmd(["git", "submodule", "update", "--init", "--recursive", path], capture_output=False)

        # 2. Stash if dirty and --force is active
        stashed = False
        if is_dirty(path) and args.force:
            print(f"Submodule '{name}' has local changes. Stashing...")
            run_cmd(["git", "stash"], cwd=path)
            stashed = True

        try:
            # 3. Fetch from remote
            print(f"Fetching updates from origin...")
            run_cmd(["git", "fetch", "origin"], cwd=path)

            # 4. Handle detached HEAD or wrong branch
            active_branch = get_current_branch(path)
            if active_branch != branch:
                print(f"Currently on active branch '{active_branch}' (expected '{branch}'). Switching...")
                try:
                    run_cmd(["git", "checkout", branch], cwd=path)
                except Exception:
                    # Try tracking remote branch if checkout failed (e.g. branch does not exist locally)
                    print(f"Creating and tracking branch '{branch}' from origin...")
                    run_cmd(["git", "checkout", "-b", branch, "--track", f"origin/{branch}"], cwd=path)

            # 5. Merge remote changes
            print(f"Merging remote changes from origin/{branch}...")
            run_cmd(["git", "merge", f"origin/{branch}"], cwd=path)

        except Exception as e:
            print(f"\033[91mError updating submodule '{name}': {e}\033[0m", file=sys.stderr)
            # If we aborted due to conflict/error, rollback merge if started
            try:
                run_cmd(["git", "merge", "--abort"], cwd=path)
            except Exception:
                pass

            if stashed:
                print(f"Restoring stashed changes...")
                try:
                    run_cmd(["git", "stash", "pop"], cwd=path)
                except Exception:
                    pass
            sys.exit(1)

        # 6. Restore stash if stashed
        if stashed:
            print(f"Restoring stashed changes...")
            try:
                run_cmd(["git", "stash", "pop"], cwd=path)
            except Exception as e:
                print(f"\033[93mWarning: Failed to restore stash pop. You may need to resolve stash conflicts in '{path}': {e}\033[0m")

        # 7. Check if pointer changed in parent
        parent_status = run_cmd(["git", "status", "--porcelain"])
        is_submodule_pointer_modified = False
        for line in parent_status.splitlines():
            # git status --porcelain prints "XY path" (first 3 chars are status flags and space)
            if len(line) > 3 and line[3:].strip() == path:
                is_submodule_pointer_modified = True
                break

        if is_submodule_pointer_modified:
            print(f"Registering updated pointer for '{name}' in parent repository...")
            run_cmd(["git", "add", path])
            commit_hash = get_current_commit(path)
            run_cmd(["git", "commit", "-m", f"chore(submodules): update {name} to {commit_hash}"])
            parent_changed = True
            print(f"\033[92mSubmodule '{name}' pointer committed to parent (hash: {commit_hash})\033[0m")
        else:
            print(f"Submodule '{name}' is already up-to-date in the parent repository.")

    # 8. Push parent repository if requested
    if parent_changed and args.push:
        print("\nPushing parent repository changes to remote...")
        run_cmd(["git", "push", "origin", "HEAD"])
        print("\033[92mParent repository pushed successfully!\033[0m")

def cmd_dev_sync(args):
    """Scenario A: Commits and pushes local modifications within submodules, then updates the parent pointers."""
    submodules = load_submodules()
    commit_msg = args.message or "chore(submodules): auto sync from development"
    parent_changed = False

    for name, sub in submodules.items():
        path = sub["path"]
        branch = sub["branch"]

        if not is_initialized(path):
            continue

        sub_dirty = is_dirty(path)
        sub_ahead = check_unpushed_commits(path, branch)

        if not sub_dirty and not sub_ahead:
            continue

        print(f"\n--- Syncing Developer Changes for '{name}' (path: '{path}', branch: '{branch}') ---")

        # 1. Commit local changes if dirty
        if sub_dirty:
            print(f"Submodule '{name}' has uncommitted changes. Committing them...")
            run_cmd(["git", "add", "-A"], cwd=path)
            try:
                run_cmd(["git", "commit", "-m", commit_msg], cwd=path)
            except Exception as e:
                print(f"Failed to commit changes inside submodule '{name}': {e}", file=sys.stderr)
                sys.exit(1)

        # 2. Push submodule changes if push requested
        if args.push:
            print(f"Pushing changes in '{name}' to origin/{branch}...")
            try:
                run_cmd(["git", "push", "origin", branch], cwd=path)
            except Exception as e:
                print(f"Failed to push changes inside submodule '{name}': {e}", file=sys.stderr)
                sys.exit(1)

        # 3. Add and commit pointer in parent repository
        print(f"Updating submodule pointer of '{name}' in parent repository...")
        run_cmd(["git", "add", path])
        commit_hash = get_current_commit(path)
        try:
            run_cmd(["git", "commit", "-m", f"chore(submodules): dev-sync {name} to {commit_hash}"])
            parent_changed = True
            print(f"\033[92mSubmodule '{name}' pointer committed to parent (hash: {commit_hash})\033[0m")
        except Exception as e:
            # Commit might have failed if git add was somehow empty or already registered
            print(f"Warning committing submodule pointer: {e}")

    # 4. Push parent repository if requested
    if parent_changed and args.push:
        print("\nPushing parent repository changes to remote...")
        run_cmd(["git", "push", "origin", "HEAD"])
        print("\033[92mParent repository pushed successfully!\033[0m")
    elif not parent_changed:
        print("\nNo local developments or updates were found in any initialized submodule.")

def cmd_sync(args):
    """Syncs submodule URLs from .gitmodules."""
    print("Syncing submodule URLs across the workspace...")
    run_cmd(["git", "submodule", "sync", "--recursive"], capture_output=False)
    print("\033[92mSubmodule URLs synchronized successfully.\033[0m")

def cmd_reset(args):
    """Resets submodules to original state specified by parent collector."""
    print("Resetting submodules to match the parent collector pointers...")
    if args.hard:
        print("\033[93mWARNING: Running hard reset! Deinitializing all submodules and forcing a fresh update...\033[0m")
        run_cmd(["git", "submodule", "deinit", "-f", "."], capture_output=False)
        run_cmd(["git", "submodule", "update", "--init", "--recursive", "--force"], capture_output=False)
    else:
        run_cmd(["git", "submodule", "update", "--init", "--recursive"], capture_output=False)
    print("\033[92mSubmodule reset completed successfully.\033[0m")

def main():
    parser = argparse.ArgumentParser(
        description="Submodule Automation Tool for C64-Intelligence-SDK",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Subcommand to execute")

    # Status subcommand
    subparsers.add_parser("status", help="Show branch, commit, and modification status for each submodule")

    # Update subcommand
    parser_update = subparsers.add_parser("update", help="Fetch remote changes, merge, and register changes in SDK collector")
    parser_update.add_argument("--force", "-f", action="store_true", help="Forcibly update by stashing local changes before updating")
    parser_update.add_argument("--push", "-p", action="store_true", help="Push parent repository changes to remote after updating")

    # Dev-sync subcommand
    parser_dev = subparsers.add_parser("dev-sync", help="Commit & push local developments in submodules, then update parent collector")
    parser_dev.add_argument("--message", "-m", type=str, help="Commit message to use when committing submodule developments")
    parser_dev.add_argument("--push", "-p", action="store_true", help="Push both submodules and parent repository to remote")

    # Sync subcommand
    subparsers.add_parser("sync", help="Synchronize submodule remote URLs with the configurations in .gitmodules")

    # Reset subcommand
    parser_reset = subparsers.add_parser("reset", help="Reset submodules to the exact commits tracked by parent repository")
    parser_reset.add_argument("--hard", action="store_true", help="Force a hard reset by de-initializing and cleanly fetching all submodules")

    args = parser.parse_args()

    # Dispatch subcommand
    if args.command == "status":
        cmd_status(args)
    elif args.command == "update":
        cmd_update(args)
    elif args.command == "dev-sync":
        cmd_dev_sync(args)
    elif args.command == "sync":
        cmd_sync(args)
    elif args.command == "reset":
        cmd_reset(args)

if __name__ == "__main__":
    main()
