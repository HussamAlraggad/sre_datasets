#!/usr/bin/env python3
"""
mini_wiki - Universal Research Assistant
Entry point script for running mini_wiki from anywhere

Usage:
    mini_wiki              # Interactive mode
    mini_wiki --tui        # TUI mode (curses-based)
    mini_wiki --demo       # Demo mode
    mini_wiki search "ml"  # Quick search
    mini_wiki version      # Show version
"""

import argparse
import json
import logging
import os
import sys
import tempfile
from pathlib import Path


def _setup_path():
    """Ensure mini_wiki package is importable regardless of working directory"""
    # Find the package root: the directory containing this script's parent
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent  # go up from mini_wiki/ to datasets/

    # Add both possible locations
    for p in [str(script_dir), str(project_root)]:
        if p not in sys.path:
            sys.path.insert(0, p)


def run_demo():
    """Run a demonstration of mini_wiki features"""
    from mini_wiki.integrated_system import MiniWikiIntegratedSystem, SystemConfig

    print("=" * 60)
    print("  mini_wiki - Universal Research Assistant")
    print("  Demo Mode")
    print("=" * 60)
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        config = SystemConfig(
            data_path=str(Path(tmpdir) / "data"),
            index_path=str(Path(tmpdir) / "index"),
            storage_path=str(Path(tmpdir) / "storage"),
        )
        system = MiniWikiIntegratedSystem(config)

        # 1. Load data
        print("1. Loading sample data...")
        system.load_data("sample_documents.csv", "csv")
        print("   ✓ Data loaded")
        print()

        # 2. Search
        print("2. Searching for 'machine learning'...")
        results = system.search("machine learning", limit=5)
        print(f"   Found {len(results)} results:")
        for i, r in enumerate(results, 1):
            print(f"   {i}. {r.get('title', 'Untitled')} (relevance: {r.get('relevance', 0):.2f})")
        print()

        # 3. Export
        print("3. Exporting results...")
        out = str(Path(tmpdir) / "results.json")
        system.export_results(results, "json", out)
        print(f"   ✓ Exported to {out}")
        print()

        # 4. Bookmarks
        print("4. Adding bookmark...")
        system.add_bookmark("Important Paper", "http://example.com", "doc1", ["ml"])
        print("   ✓ Bookmark added")
        print()

        # 5. Stats
        print("5. System statistics...")
        stats = system.get_statistics()
        print(f"   Searches: {stats['total_searches']}, Bookmarks: {stats['bookmarks_count']}")
        print()

        # 6. Health
        print("6. Health check...")
        health = system.health_check()
        print(f"   Status: {health['status']}")
        print()

    print("=" * 60)
    print("  Demo completed!")
    print("=" * 60)


def run_tui():
    """Run the TUI interface using curses"""
    from mini_wiki.ui.tui_app import CursesTUI
    tui = CursesTUI()
    tui.start()


def run_interactive():
    """Run in interactive REPL mode"""
    from mini_wiki.integrated_system import MiniWikiIntegratedSystem, SystemConfig

    print("=" * 60)
    print("  mini_wiki - Universal Research Assistant")
    print("  Interactive Mode")
    print("=" * 60)
    print()
    print("Type 'help' for commands, 'quit' to exit")
    print()

    system = MiniWikiIntegratedSystem(SystemConfig())

    while True:
        try:
            try:
                command = input("mini_wiki> ").strip()
            except EOFError:
                print("\nGoodbye!")
                break

            if not command:
                continue

            parts = command.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if cmd in ("quit", "exit", "q"):
                print("Goodbye!")
                break
            elif cmd == "help":
                print()
                print("Commands:")
                print("  search <query>    Search documents")
                print("  load <path>       Load data file")
                print("  export <fmt>      Export results (json/md/csv)")
                print("  bookmark <title>  Add bookmark")
                print("  bookmarks         List bookmarks")
                print("  history           Show search history")
                print("  stats             System statistics")
                print("  health            Health check")
                print("  optimize          Optimize performance")
                print("  quit              Exit")
                print()
            elif cmd == "search":
                if not arg:
                    print("Usage: search <query>")
                    continue
                results = system.search(arg)
                print(f"Found {len(results)} results:")
                for i, r in enumerate(results, 1):
                    print(f"  {i}. {r.get('title', 'Untitled')} (relevance: {r.get('relevance', 0):.2f})")
            elif cmd == "load":
                if not arg:
                    print("Usage: load <path>")
                    continue
                ok = system.load_data(arg, "auto")
                print("✓ Loaded" if ok else "✗ Failed to load")
            elif cmd == "export":
                fmt = arg or "json"
                out = f"results.{fmt}"
                system.export_results([], fmt, out)
                print(f"Exported to {out}")
            elif cmd == "bookmark":
                system.add_bookmark(arg or "Untitled", "http://example.com", "doc1")
                print("✓ Bookmark added")
            elif cmd == "bookmarks":
                for b in system.get_bookmarks():
                    print(f"  - {b.get('title', 'Untitled')}")
            elif cmd == "history":
                for h in system.get_search_history():
                    print(f"  - {h.get('query', '?')}")
            elif cmd == "stats":
                for k, v in system.get_statistics().items():
                    print(f"  {k}: {v}")
            elif cmd == "health":
                h = system.health_check()
                print(f"Status: {h['status']}")
            elif cmd == "optimize":
                system.optimize_performance()
                print("✓ Optimized")
            else:
                print(f"Unknown command: {cmd}. Type 'help' for commands.")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break


def run_search(query, limit=10, fmt="text"):
    """Quick search from command line"""
    from mini_wiki.integrated_system import MiniWikiIntegratedSystem, SystemConfig

    system = MiniWikiIntegratedSystem(SystemConfig())
    results = system.search(query, limit=limit)

    if fmt == "json":
        print(json.dumps(results, indent=2))
    else:
        for i, r in enumerate(results, 1):
            title = r.get("title", "Untitled")
            score = r.get("relevance", 0)
            print(f"{i}. {title} (score: {score:.2f})")


def main():
    """Main entry point"""
    _setup_path()

    parser = argparse.ArgumentParser(
        prog="mini_wiki",
        description="mini_wiki - Universal Research Assistant",
    )
    parser.add_argument("--tui", action="store_true", help="Launch interactive TUI (curses)")
    parser.add_argument("--demo", action="store_true", help="Run demo")
    parser.add_argument("--interactive", action="store_true", help="Interactive REPL mode")
    parser.add_argument("command", nargs="?", help="Command: search, version")
    parser.add_argument("args", nargs="*", help="Command arguments")

    args = parser.parse_args()

    if args.demo:
        run_demo()
    elif args.tui:
        run_tui()
    elif args.interactive:
        run_interactive()
    elif args.command == "search":
        query = " ".join(args.args) if args.args else ""
        if not query:
            print("Usage: mini_wiki search <query>")
            sys.exit(1)
        run_search(query)
    elif args.command == "version":
        from mini_wiki import __version__
        print(f"mini_wiki v{__version__}")
    else:
        # Default: launch TUI if terminal supports it, otherwise interactive
        run_interactive()


if __name__ == "__main__":
    main()