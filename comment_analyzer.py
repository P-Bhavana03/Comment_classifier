import json
import os
import time
import argparse
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import types
import logging
import matplotlib.pyplot as plt
from better_profanity import profanity


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


load_dotenv()


INPUT_FILE = "comments.json"
OUTPUT_FILE = "analyzed_comments.json"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_NAME = "gemini-1.5-flash"
MAX_RETRIES = 3
RETRY_DELAY = 5


def load_comments(filepath):
    """Loads comments from a JSON file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            comments = json.load(f)
        logging.info(f"Successfully loaded {len(comments)} comments from {filepath}")
        return comments
    except FileNotFoundError:
        logging.error(f"Error: Input file not found at {filepath}")
        return None
    except json.JSONDecodeError:
        logging.error(f"Error: Could not decode JSON from {filepath}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while loading comments: {e}")
        return None


def configure_genai():
    """Configures the Generative AI client."""
    if not GEMINI_API_KEY:
        logging.error("Error: GEMINI_API_KEY not found in environment variables.")
        logging.info("Please create a .env file with GEMINI_API_KEY=YOUR_API_KEY_HERE")
        return None
    try:
        genai.configure(api_key=GEMINI_API_KEY)

        logging.info("Google GenAI client configured successfully.")
        return genai
    except Exception as e:
        logging.error(f"Error configuring Google GenAI client: {e}")
        return None


def analyze_comment_with_retry(client, model_name, comment_text):
    """Analyzes a single comment using the Gemini API with retry logic."""
    prompt = f"""
    Analyze the following user comment and determine if it is offensive.
    Provide your analysis in JSON format with the following fields:
    - "is_offensive": boolean (true if offensive, false otherwise)
    - "offense_type": string (e.g., "hate speech", "toxicity", "profanity", "harassment", "spam", "none")
    - "explanation": string (a brief explanation for the classification)
    - "severity": integer (estimated severity from 1-5, 5 being most severe; 0 if not offensive)

    Comment: "{comment_text}"

    JSON Response:
    """

    model = client.GenerativeModel(model_name)
    generation_config = types.GenerationConfig(response_mime_type="application/json")

    for attempt in range(MAX_RETRIES):
        try:
            response = model.generate_content(
                prompt, generation_config=generation_config
            )

            if not response.parts:
                logging.warning(
                    f"Received empty response or safety block for comment: '{comment_text[:50]}...' - classifying as potentially problematic."
                )

                return {
                    "is_offensive": True,
                    "offense_type": "blocked/unclear",
                    "explanation": "Model response was blocked or empty, potentially due to sensitive content.",
                    "severity": 3,
                }

            analysis_json = json.loads(response.text)

            if not all(
                k in analysis_json
                for k in ["is_offensive", "offense_type", "explanation", "severity"]
            ):
                logging.warning(
                    f"Received incomplete JSON from API for comment: '{comment_text[:50]}...'. Retrying..."
                )
                raise ValueError("Incomplete JSON structure")

            logging.debug(f"Successfully analyzed comment: '{comment_text[:50]}...'")
            return analysis_json

        except types.generation_types.BlockedPromptException as bpe:
            logging.warning(
                f"Prompt blocked for comment: '{comment_text[:50]}...'. Classifying as offensive. Reason: {bpe}"
            )
            return {
                "is_offensive": True,
                "offense_type": "blocked",
                "explanation": f"Prompt blocked by safety filters. Reason: {bpe}",
                "severity": 4,
            }
        except types.generation_types.StopCandidateException as sce:
            logging.warning(
                f"Content generation stopped for comment: '{comment_text[:50]}...'. Classifying as potentially problematic. Reason: {sce}"
            )
            return {
                "is_offensive": True,
                "offense_type": "stopped",
                "explanation": f"Content generation stopped, potentially due to policy violation. Reason: {sce}",
                "severity": 3,
            }
        except json.JSONDecodeError as jde:
            logging.warning(
                f"Failed to decode JSON response from API for comment: '{comment_text[:50]}...'. Response text: {response.text}. Error: {jde}. Attempt {attempt + 1}/{MAX_RETRIES}"
            )
            if attempt + 1 == MAX_RETRIES:
                logging.error(
                    f"Failed to get valid JSON after {MAX_RETRIES} attempts for comment: '{comment_text[:50]}...'"
                )
                return None
            time.sleep(RETRY_DELAY)
        except Exception as e:
            logging.warning(
                f"Error analyzing comment '{comment_text[:50]}...': {e}. Attempt {attempt + 1}/{MAX_RETRIES}"
            )
            if attempt + 1 == MAX_RETRIES:
                logging.error(
                    f"Failed to analyze comment after {MAX_RETRIES} attempts: '{comment_text[:50]}...'"
                )
                return None
            time.sleep(RETRY_DELAY)
    return None


def save_analyzed_comments(filepath, data):
    """Saves the analyzed comments to a JSON file."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logging.info(f"Successfully saved analyzed comments to {filepath}")
    except IOError as e:
        logging.error(f"Error writing analyzed comments to {filepath}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred while saving comments: {e}")


def generate_report(analyzed_comments):
    """Generates and prints a summary report."""
    if not analyzed_comments:
        logging.warning("No analyzed comments to generate a report for.")
        return

    offensive_comments = [
        c for c in analyzed_comments if c.get("analysis", {}).get("is_offensive")
    ]
    num_offensive = len(offensive_comments)
    total_comments = len(analyzed_comments)

    print("\n--- Comment Analysis Report ---")
    print(f"Total comments processed: {total_comments}")
    print(f"Number of offensive comments detected: {num_offensive}")

    if num_offensive > 0:
        print("\nOffense Type Breakdown:")
        offense_counts = {}
        for comment in offensive_comments:
            offense_type = comment.get("analysis", {}).get("offense_type", "unknown")
            offense_counts[offense_type] = offense_counts.get(offense_type, 0) + 1

        for offense_type, count in sorted(offense_counts.items()):
            print(f"- {offense_type.capitalize()}: {count}")

        print("\nTop 5 Most Offensive Comments (by estimated severity):")
        offensive_comments.sort(
            key=lambda x: x.get("analysis", {}).get("severity", 0), reverse=True
        )
        for i, comment in enumerate(offensive_comments[:5]):
            print(
                f"{i+1}. ID: {comment['comment_id']}, User: {comment['username']}, Severity: {comment.get('analysis', {}).get('severity', 'N/A')}"
            )
            print(f"   Comment: {comment['comment_text']}")
            print(
                f"   Type: {comment.get('analysis', {}).get('offense_type', 'N/A')}, Explanation: {comment.get('analysis', {}).get('explanation', 'N/A')}"
            )
            print("-" * 10)

    if num_offensive > 0:
        try:
            types = list(offense_counts.keys())
            counts = list(offense_counts.values())

            plt.figure(figsize=(10, 6))
            bars = plt.bar(types, counts, color="skyblue")
            plt.xlabel("Offense Type")
            plt.ylabel("Number of Comments")
            plt.title("Distribution of Offensive Comment Types")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()

            for bar in bars:
                yval = bar.get_height()
                plt.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    yval,
                    int(yval),
                    va="bottom",
                    ha="center",
                )

            chart_filename = "offense_distribution.png"
            plt.savefig(chart_filename)
            logging.info(f"Saved offense distribution chart to {chart_filename}")
            plt.close()
        except Exception as e:
            logging.error(f"Failed to generate or save offense distribution chart: {e}")

    print("--- End of Report ---")


def main():
    """Main function to run the comment analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze user comments for offensive content."
    )
    parser.add_argument(
        "-i",
        "--input",
        default=INPUT_FILE,
        help=f"Path to the input JSON file containing comments (default: {INPUT_FILE})",
    )
    args = parser.parse_args()
    input_filepath = args.input

    logging.info(
        f"Starting comment analysis process using input file: {input_filepath}..."
    )

    genai_client = configure_genai()
    if not genai_client:
        return

    comments = load_comments(input_filepath)
    if comments is None:
        return

    print(f"\n--- Initial Summary ---")
    print(f"Total comments loaded: {len(comments)}")
    if comments:
        print("Sample comments:")
        for i, comment in enumerate(comments[:3]):
            print(
                f"  {i+1}. ID: {comment['comment_id']}, User: {comment['username']}, Text: {comment['comment_text'][:60]}..."
            )
    print("-" * 20 + "\n")

    profanity.load_censor_words()
    logging.info("Initialized profanity checker.")

    logging.info("Starting comment analysis (with profanity pre-check)...")
    analyzed_comments = []
    processed_count = 0
    failed_count = 0
    pre_filtered_count = 0

    for comment in comments:
        comment_text = comment.get("comment_text")
        if not comment_text:
            logging.warning(
                f"Skipping comment ID {comment.get('comment_id')} due to missing 'comment_text'."
            )
            comment["analysis"] = {"error": "Missing comment text"}
            analyzed_comments.append(comment)
            failed_count += 1
            continue

        if profanity.contains_profanity(comment_text):
            logging.info(
                f"Profanity detected in comment ID: {comment.get('comment_id')}. Skipping API call."
            )
            analysis_result = {
                "is_offensive": True,
                "offense_type": "profanity",
                "explanation": "Detected by profanity pre-filter.",
                "severity": 3,
            }
            pre_filtered_count += 1
        else:

            logging.info(
                f"Analyzing comment ID: {comment.get('comment_id')} via Gemini API..."
            )
            analysis_result = analyze_comment_with_retry(
                genai_client, MODEL_NAME, comment_text
            )

            if analysis_result:
                processed_count += 1
            else:
                comment["analysis"] = {"error": "Failed to analyze after retries"}
                failed_count += 1
                logging.error(
                    f"Failed to analyze comment ID: {comment.get('comment_id')}"
                )

        if analysis_result:
            comment["analysis"] = analysis_result

        analyzed_comments.append(comment)

    logging.info(
        f"Analysis complete. Pre-filtered (profanity): {pre_filtered_count}, Processed via API: {processed_count}, Failed: {failed_count}"
    )

    save_analyzed_comments(OUTPUT_FILE, analyzed_comments)
    generate_report(analyzed_comments)

    logging.info("Comment analysis process finished.")


if __name__ == "__main__":
    main()
