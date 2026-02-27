#!/usr/bin/env python3
"""
Apify Actor entry point for web2json-agent
Reads input from Apify, runs the parser generator, and saves results to dataset
"""
import os
import sys
import json
import base64
import tempfile
import shutil
import traceback
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from web2json.main import main as web2json_main


def get_apify_input():
    """Read input from Apify Actor input"""
    # Apify standard input locations
    possible_paths = [
        os.environ.get("APIFY_INPUT_PATH"),  # Custom path if set
        "/apify_storage/key_value_stores/default/INPUT.json",  # Standard Apify location
        "apify_storage/key_value_stores/default/INPUT.json",  # Relative path
        "INPUT.json",  # Fallback
    ]

    for input_path in possible_paths:
        if input_path and os.path.exists(input_path):
            logger.info(f"Reading input from: {input_path}")
            with open(input_path, "r", encoding="utf-8") as f:
                return json.load(f)

    logger.warning("No input file found, using empty default. Please provide input in Apify Console.")
    return {}


def save_to_dataset(data):
    """Save data to Apify dataset"""
    dataset_dir = os.environ.get("APIFY_DEFAULT_DATASET_ID", "default")
    dataset_path = Path(f"apify_storage/datasets/{dataset_dir}")
    dataset_path.mkdir(parents=True, exist_ok=True)

    # Find next file number
    existing_files = list(dataset_path.glob("*.json"))
    next_num = len(existing_files) + 1

    output_file = dataset_path / f"{next_num:09d}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved data to {output_file}")


def main():
    """Main entry point for Apify Actor"""
    logger.info("Starting web2json-agent Apify Actor")

    # Get input from Apify
    actor_input = get_apify_input()
    logger.info(f"Received input: {json.dumps(actor_input, indent=2)}")

    # Parse input parameters
    input_mode = actor_input.get("inputMode", "html")
    domain = actor_input.get("domain", "apify_output")
    iteration_rounds = actor_input.get("iterationRounds", 3)
    cluster_mode = actor_input.get("clusterMode", False)
    schema_mode = actor_input.get("schemaMode", "auto")
    predefined_schema = actor_input.get("predefinedSchema")

    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        input_dir = Path(temp_dir) / "input_html"
        output_dir = Path(temp_dir) / "output"
        input_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Handle different input modes
            if input_mode == "html":
                # Decode base64 HTML files
                html_files = actor_input.get("htmlFiles", [])
                if not html_files:
                    raise ValueError("No HTML files provided in input")

                for idx, file_data in enumerate(html_files):
                    filename = file_data.get("filename", f"page_{idx+1}.html")
                    content_b64 = file_data.get("content", "")

                    # Decode base64 content
                    try:
                        html_content = base64.b64decode(content_b64).decode("utf-8")
                    except Exception as e:
                        logger.warning(f"Failed to decode {filename}, trying as plain text: {e}")
                        html_content = content_b64

                    # Save to input directory
                    input_file = input_dir / filename
                    with open(input_file, "w", encoding="utf-8") as f:
                        f.write(html_content)

                    logger.info(f"Saved HTML file: {filename}")

            elif input_mode == "url":
                # Fetch URLs and save HTML
                urls = actor_input.get("urls", [])
                if not urls:
                    raise ValueError("No URLs provided in input")

                import requests
                from bs4 import BeautifulSoup

                for idx, url in enumerate(urls):
                    try:
                        response = requests.get(url, timeout=30)
                        response.raise_for_status()
                        html_content = response.text

                        # Save to input directory
                        filename = f"page_{idx+1}.html"
                        input_file = input_dir / filename
                        with open(input_file, "w", encoding="utf-8") as f:
                            f.write(html_content)

                        logger.info(f"Fetched and saved: {url}")
                    except Exception as e:
                        logger.error(f"Failed to fetch {url}: {e}")

            else:
                raise ValueError(f"Invalid input mode: {input_mode}")

            # Check if any files were saved
            input_files = list(input_dir.glob("*.html"))
            if not input_files:
                raise ValueError("No HTML files were successfully processed")

            logger.info(f"Total input files: {len(input_files)}")

            # Build web2json command arguments
            args = [
                "-d", str(input_dir),
                "-o", str(output_dir / domain),
                "--iteration-rounds", str(iteration_rounds)
            ]

            if domain:
                args.extend(["--domain", domain])

            if cluster_mode:
                args.append("--cluster")

            # Save predefined schema if provided
            if schema_mode == "predefined" and predefined_schema:
                schema_file = Path(temp_dir) / "predefined_schema.json"
                with open(schema_file, "w", encoding="utf-8") as f:
                    json.dump(predefined_schema, f, indent=2)
                args.extend(["--schema-template", str(schema_file)])

            # Run web2json-agent
            logger.info(f"Running web2json with args: {' '.join(args)}")

            # Import and run the main function
            original_argv = sys.argv
            sys.argv = ["web2json"] + args

            try:
                web2json_main()
            finally:
                sys.argv = original_argv

            # Collect results and save to Apify dataset
            result_dir = output_dir / domain / "result"
            if result_dir.exists():
                for result_file in result_dir.glob("*.json"):
                    with open(result_file, "r", encoding="utf-8") as f:
                        result_data = json.load(f)

                    # Add metadata
                    result_data["_metadata"] = {
                        "source_file": result_file.name,
                        "domain": domain,
                        "timestamp": result_file.stat().st_mtime
                    }

                    save_to_dataset(result_data)

                logger.info(f"Saved {len(list(result_dir.glob('*.json')))} results to dataset")
            else:
                logger.warning("No results found in output directory")

            # Also save parser code to dataset for reference
            parser_file = output_dir / domain / "parsers" / "final_parser.py"
            if parser_file.exists():
                with open(parser_file, "r", encoding="utf-8") as f:
                    parser_code = f.read()

                save_to_dataset({
                    "_type": "parser_code",
                    "domain": domain,
                    "parser": parser_code
                })

            logger.info("Web2JSON Agent completed successfully")

        except Exception as e:
            logger.error(f"Error during execution: {e}", exc_info=True)
            save_to_dataset({
                "_type": "error",
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            sys.exit(1)


if __name__ == "__main__":
    main()
