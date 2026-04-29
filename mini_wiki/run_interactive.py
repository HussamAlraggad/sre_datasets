#!/usr/bin/env python3
"""
mini_wiki - Universal Research Assistant
Entry point script for running mini_wiki

Usage:
    python3 mini_wiki/run_interactive.py          # Interactive mode
    python3 mini_wiki/run_interactive.py --tui     # TUI mode
    python3 mini_wiki/run_interactive.py --demo     # Demo mode
"""

import argparse
import json
import logging
import sys
import tempfile
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_demo():
    """Run a demonstration of mini_wiki features"""
    print("=" * 60)
    print("  mini_wiki - Universal Research Assistant")
    print("  Demo Mode")
    print("=" * 60)
    print()

    # Import integrated system
    from mini_wiki.integrated_system import MiniWikiIntegratedSystem, SystemConfig

    # Create system with temporary storage
    with tempfile.TemporaryDirectory() as tmpdir:
        config = SystemConfig(
            data_path=str(Path(tmpdir) / "data"),
            index_path=str(Path(tmpdir) / "index"),
            storage_path=str(Path(tmpdir) / "storage"),
            theme="dark",
            max_results=10,
        )
        system = MiniWikiIntegratedSystem(config)

        # 1. Load sample data
        print("1. Loading sample data...")
        system.load_data("sample_documents.csv", "csv")
        system.load_data("sample_papers.json", "json")
        print("   ✓ Data loaded successfully")
        print()

        # 2. Search
        print("2. Searching for 'machine learning'...")
        results = system.search("machine learning", limit=5)
        print(f"   Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            title = result.get("title", "Untitled")
            relevance = result.get("relevance", 0)
            print(f"   {i}. {title} (relevance: {relevance:.2f})")
        print()

        # 3. Search with filters
        print("3. Searching with filters (min_relevance=0.7)...")
        filtered_results = system.search(
            "python",
            limit=5,
            filter_criteria={"min_relevance": 0.7},
        )
        print(f"   Found {len(filtered_results)} filtered results")
        print()

        # 4. Export results
        print("4. Exporting results...")
        output_path = str(Path(tmpdir) / "results.json")
        success = system.export_results(results, "json", output_path)
        if success:
            print(f"   ✓ Results exported to {output_path}")
        else:
            print("   ✗ Export failed")
        print()

        # 5. Add bookmarks
        print("5. Adding bookmarks...")
        if results:
            system.add_bookmark(
                title=results[0].get("title", "Untitled"),
                url="http://example.com",
                document_id=results[0].get("id", "1"),
                tags=["important", "research"],
            )
            print("   ✓ Bookmark added")
        print()

        # 6. Search history
        print("6. Search history...")
        history = system.get_search_history(limit=5)
        print(f"   {len(history)} search entries in history")
        print()

        # 7. Recent items
        print("7. Recent items...")
        recent = system.get_recent_items(limit=5)
        print(f"   {len(recent)} recent items")
        print()

        # 8. Statistics
        print("8. System statistics...")
        stats = system.get_statistics()
        print(f"   Total searches: {stats['total_searches']}")
        print(f"   Bookmarks: {stats['bookmarks_count']}")
        print()

        # 9. Health check
        print("9. Health check...")
        health = system.health_check()
        print(f"   System status: {health['status']}")
        for component, status in health["components"].items():
            print(f"   {component}: {status}")
        print()

        # 10. Optimize performance
        print("10. Optimizing performance...")
        system.optimize_performance()
        print("   ✓ Performance optimized")
        print()

    print("=" * 60)
    print("  Demo completed successfully!")
    print("=" * 60)


def run_tui():
    """Run the TUI interface using curses"""
    try:
        from mini_wiki.ui.tui_app import CursesTUI
        tui = CursesTUI()
        tui.start()
    except ImportError as e:
        print(f"TUI dependencies not available: {e}")
        print("Falling back to interactive mode...")
        run_interactive()
    except Exception as e:
        print(f"TUI error: {e}")
        print("Falling back to interactive mode...")
        run_interactive()


def run_interactive():
    """Run in interactive mode"""
    from mini_wiki.integrated_system import MiniWikiIntegratedSystem, SystemConfig

    print("=" * 60)
    print("  mini_wiki - Universal Research Assistant")
    print("  Interactive Mode")
    print("=" * 60)
    print()
    print("Type 'help' for available commands, 'quit' to exit")
    print()

    # Create system
    config = SystemConfig()
    system = MiniWikiIntegratedSystem(config)

    while True:
        try:
            try:
                command = input("mini_wiki> ").strip()
            except EOFError:
                print("\nGoodbye!")
                break

            if not command:
                continue

            if command == "quit" or command == "exit":
                print("Goodbye!")
                break

            elif command == "help":
                print()
                print("Available commands:")
                print("  help              - Show this help message")
                print("  load <path>       - Load data from file")
                print("  search <query>    - Search documents")
                print("  export <format>   - Export last results (json/md/csv)")
                print("  bookmark <title>  - Add bookmark")
                print("  bookmarks         - List bookmarks")
                print("  history           - Show search history")
                print("  stats             - Show system statistics")
                print("  health            - Show system health")
                print("  optimize          - Optimize performance")
                print("  quit              - Exit mini_wiki")
                print()

            elif command.startswith("load "):
                path = command[5:].strip()
                print(f"Loading data from {path}...")
                success = system.load_data(path, "auto")
                if success:
                    print("✓ Data loaded successfully")
                else:
                    print("✗ Failed to load data")

            elif command.startswith("search "):
                query = command[7:].strip()
                print(f"Searching for '{query}'...")
                results = system.search(query)
                print(f"Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    title = result.get("title", "Untitled")
                    relevance = result.get("relevance", 0)
                    print(f"  {i}. {title} (relevance: {relevance:.2f})")

            elif command.startswith("export "):
                fmt = command[7:].strip()
                print(f"Exporting results as {fmt}...")
                output_path = f"results.{fmt}"
                success = system.export_results([], fmt, output_path)
                if success:
                    print(f"✓ Results exported to {output_path}")
                else:
                    print("✗ Export failed")

            elif command.startswith("bookmark "):
                title = command[9:].strip()
                print(f"Adding bookmark '{title}'...")
                system.add_bookmark(title, "http://example.com", "doc1")
                print("✓ Bookmark added")

            elif command == "bookmarks":
                bookmarks = system.get_bookmarks()
                print(f"Bookmarks ({len(bookmarks)}):")
                for bookmark in bookmarks:
                    print(f"  - {bookmark.get('title', 'Untitled')}")

            elif command == "history":
                history = system.get_search_history()
                print(f"Search history ({len(history)} entries):")
                for entry in history:
                    print(f"  - {entry.get('query', 'Unknown')}")

            elif command == "stats":
                stats = system.get_statistics()
                print("System statistics:")
                for key, value in stats.items():
                    print(f"  {key}: {value}")

            elif command == "health":
                health = system.health_check()
                print(f"System status: {health['status']}")
                for component, status in health["components"].items():
                    print(f"  {component}: {status}")

            elif command == "optimize":
                system.optimize_performance()
                print("✓ Performance optimized")

            else:
                print(f"Unknown command: {command}")
                print("Type 'help' for available commands")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="mini_wiki - Universal Research Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 mini_wiki/run_interactive.py --demo     Run demo
  python3 mini_wiki/run_interactive.py --tui      Run TUI mode
  python3 mini_wiki/run_interactive.py            Run interactive mode
        """,
    )
    parser.add_argument(
        "--demo", action="store_true", help="Run demonstration mode"
    )
    parser.add_argument(
        "--tui", action="store_true", help="Run TUI mode"
    )
    parser.add_argument(
        "--config", type=str, help="Configuration file path"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.demo:
        run_demo()
    elif args.tui:
        run_tui()
    else:
        run_interactive()


if __name__ == "__main__":
    main()