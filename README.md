# Comment Classifier using Google Gemini

This Python application reads user comments from a JSON file, uses the Google Gemini API to detect offensive content, classifies the offense type, provides an explanation, estimates severity, and generates a report of flagged comments.

## Features

- Reads comments from a JSON input file (`comments.json`).
- Uses Google Gemini (`gemini-1.5-flash` model) for analysis.
- Detects if a comment is offensive.
- Classifies offense type (e.g., hate speech, toxicity, profanity, harassment, spam, none).
- Provides a brief explanation for the classification.
- Estimates severity on a scale of 1-5.
- Handles API errors and retries.
- Outputs analyzed data to a new JSON file (`analyzed_comments.json`).
- Prints a summary report to the console.
- **New:** Accepts input file path via CLI argument (`--input` or `-i`).
- **New:** Pre-filters comments using the `better-profanity` library to quickly flag obvious profanity.
- **New:** Generates a bar chart (`offense_distribution.png`) visualizing the distribution of detected offense types.

## Project Structure

```
Comment_classifier/
├── .env.example        # Example environment file
├── .gitignore          # Git ignore file
├── comments.json       # Sample input comments
├── comment_analyzer.py # Main Python script
├── requirements.txt    # Python dependencies
├── analyzed_comments.json # Output file (generated after running)
├── offense_distribution.png # Output chart (generated after running, if offensive comments found)
└── README.md           # This file
```

## Setup Instructions

1.  **Clone the repository (or download the files):**
    Get the project files onto your local machine.

2.  **Create a Virtual Environment (Recommended):**
    Open your terminal in the project directory and run:

    ```bash
    python -m venv venv
    ```

    Activate the environment:

    - Windows: `.\venv\Scripts\activate`
    - macOS/Linux: `source venv/bin/activate`

3.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Environment Variables:**
    - Rename the `.env.example` file to `.env`.
    - Open the `.env` file and replace `YOUR_API_KEY_HERE` with your actual Google Gemini API key.
      ```
      GEMINI_API_KEY=YOUR_ACTUAL_API_KEY
      ```

## How to Use

1.  **Prepare Input Data:**

    - Ensure you have a JSON file containing comments in the project directory (default is `comments.json`).
    - The file should be a JSON array of objects, each with `comment_id`, `username`, and `comment_text` fields. A sample file is provided.

2.  **Run the Script:**
    Make sure your virtual environment is activated and you are in the project directory. Execute the script from your terminal. You can optionally specify the input file:

    ```bash
    # Use default input file (comments.json)
    python comment_analyzer.py

    # Specify a different input file
    python comment_analyzer.py --input path/to/your/comments.json
    # Or using the short flag
    python comment_analyzer.py -i path/to/your/comments.json
    ```

3.  **View Results:**
    - The script will print logs and a summary report to the console during execution.
    - An `analyzed_comments.json` file will be created (or overwritten) in the project directory. This file contains the original comment data along with the added `analysis` field for each comment.
    - If offensive comments are detected, an `offense_distribution.png` image file will be created (or overwritten), showing a bar chart of the offense types.

## Sample Output

### Console Report

The script will print a report similar to this:

```
--- Initial Summary ---
Total comments loaded: 10
Sample comments:
  1. ID: 1, User: user123, Text: This is a great post! Very informative....
  2. ID: 2, User: trollMaster, Text: You are an idiot, nobody cares about your opinion....
  3. ID: 3, User: helpfulHannah, Text: Could you please clarify point number 3?...
--------------------

INFO:root:Starting comment analysis using Gemini API...
INFO:root:Analyzing comment ID: 1...
INFO:root:Analyzing comment ID: 2...
... (logs for each comment) ...
INFO:root:Analysis complete. Processed: 10, Failed: 0

--- Comment Analysis Report ---
Total comments processed: 10
Number of offensive comments detected: 4

Offense Type Breakdown:
- Hate speech: 1
- Profanity: 1
- Toxicity: 2

Top 5 Most Offensive Comments (by estimated severity):
1. ID: 8, User: haterHarry, Severity: 5
   Comment: People like you should just disappear. You're worthless.
   Type: hate speech, Explanation: The comment expresses extreme hostility and wishes harm upon a group or individual.
----------
2. ID: 10, User: offensiveOscar, Severity: 4
   Comment: Go back to where you came from, you don't belong here.
   Type: hate speech, Explanation: This comment uses xenophobic language to attack someone based on their perceived origin.
----------
3. ID: 16, User: harassingHenry, Severity: 4
   Comment: I know where you live. Watch your back.
   Type: harassment, Explanation: The comment is a direct threat and could be interpreted as a form of harassment or stalking.  It implies knowledge of the user's location and suggests potential harm.
----------
4. ID: 2, User: trollMaster, Severity: 3
   Comment: You are an idiot, nobody cares about your opinion.
   Type: toxicity, Explanation: The comment contains an insult ("idiot") and a dismissive remark ("nobody cares about your opinion"), which are both considered toxic and offensive.
----------
5. ID: 18, User: profanePaul, Severity: 3
   Comment: What the hell is wrong with you? This is ridiculous.
   Type: profanity, Explanation: Detected by profanity pre-filter.
----------
--- End of Report ---
INFO:root:Comment analysis process finished.
```

### `analyzed_comments.json` File

The output file will contain the original comments plus the analysis results:

```json
[
  {
    "comment_id": 1,
    "username": "user123",
    "comment_text": "This is a great post! Very informative.",
    "analysis": {
      "is_offensive": false,
      "offense_type": "none",
      "explanation": "The comment is positive and expresses appreciation.",
      "severity": 0
    }
  },
  {
    "comment_id": 2,
    "username": "trollMaster",
    "comment_text": "You are an idiot, nobody cares about your opinion.",
    "analysis": {
      "is_offensive": true,
      "offense_type": "toxicity",
      "explanation": "The comment uses insulting language ('idiot') to attack the user directly.",
      "severity": 3
    }
  },
  // ... other comments ...
  {
    "comment_id": 10,
    "username": "offensiveOscar",
    "comment_text": "Go back to where you came from, you don't belong here.",
    "analysis": {
      "is_offensive": true,
      "offense_type": "hate speech",
      "explanation": "This comment uses xenophobic language to attack someone based on their perceived origin.",
      "severity": 4
    }
  }
]
```
