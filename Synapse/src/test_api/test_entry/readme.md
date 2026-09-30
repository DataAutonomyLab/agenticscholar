1. **Prepare Paper Files**
   Place the Markdown files of the papers to be evaluated in the `md_files` folder.
   Make sure the filenames match the paper IDs listed in `"paper_lists"`.

2. **Configure LLM API**
   Set up your LLM API credentials in `config.ini`.

3. **Run Evaluation**
   Use the `QA_evaluation` function in `QA_evaluation.py` to perform the evaluation.
   **⚠️ Important:** Make sure the file paths are correct when calling the function, otherwise the evaluation may fail.

4. **View Results**
   The evaluation results will be saved in the `evaluation-output` folder.
   Each output file is named according to the corresponding `"query_id"`.
