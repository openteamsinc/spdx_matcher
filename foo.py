import sys
import argparse
from spdx_matcher.all_matches import find_best_matches


def main():
    parser = argparse.ArgumentParser(description="Find best matching SPDX license templates for license text")
    parser.add_argument("input_file", help="Path to file containing license text to match")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output during matching")

    args = parser.parse_args()

    # Read the input file
    try:
        with open(args.input_file, "r", encoding="utf-8") as f:
            license_text = f.read()
    except Exception as e:
        print(f"Error reading input file '{args.input_file}': {e}")
        sys.exit(1)

    print(f"Analyzing license text from {args.input_file}...")
    print()

    # Find best matches
    best_matches = find_best_matches(license_text, verbose=args.verbose)

    if not best_matches:
        print("No matches found.")
        sys.exit(1)

    print(f"Best {len(best_matches)} match(es) (ranked by completeness):")
    print()

    for i, (license_id, remaining_text, remaining_chars) in enumerate(best_matches, 1):
        if remaining_chars == 0:
            print(f"{i:2d}. {license_id} - EXACT MATCH ✓")
        else:
            coverage = max(0, 100 - (remaining_chars / len(license_text) * 100))
            print(f"{i:2d}. {license_id} - {coverage:.1f}% coverage ({remaining_chars} chars remaining)")

            if i <= 3 and remaining_text.strip():  # Show remaining text for top 3 matches
                rt = remaining_text.strip()
                print(f"    Remaining text: {rt[:100]}{'...' if len(rt) > 100 else ''}")
                print()


if __name__ == "__main__":
    main()
