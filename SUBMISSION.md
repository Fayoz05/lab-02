# Start, check, and submit

## 1. Set up Python

Use Python 3.12. Open a terminal in the lab folder: the folder containing README.md.

```bash
python -m venv .venv
```

Activate the environment. Run **only** the command for your system:

| System | Command |
|---|---|
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows Command Prompt | `.venv\Scripts\activate.bat` |
| Linux/macOS | `source .venv/bin/activate` |

Then install the lab packages:

```bash
python -m pip install -r requirements.txt
```

Use your university's notebook system, or install a local notebook interface:

```bash
python -m pip install jupyterlab ipykernel
python -m jupyterlab
```

Select the Python environment with the lab packages. Open `notebooks/lab.ipynb`.
You can also use a notebook-capable editor such as VS Code.

## 2. Complete the lab

1. Read README.md for the tasks and FUNCTION_GUIDE.md for exact rules.
2. Write missing functions in `src/solution.py`. Do not rename them.
3. The notebook first runs setup only. After writing a function, remove `#` from its
   example call and run it. Add your own analysis and explanations.
4. Copy `REPORT_TEMPLATE.md` to `REPORT.md` and answer its questions.
5. Save required tables and figures in `outputs/`.
6. Complete `AI_USE.md`, including `No AI assistance` if you did not use AI. Warning: if you lie about your use of AI, your work will not be accepted.
7. Add the extra tests and experiments requested by your lab.

## 3. Check your work

From the lab folder, run:

```bash
python -m unittest discover -s tests -p 'test_public.py' -v
```

Tests fail before the missing functions are written. This is expected.
A green check does not guarantee full marks: the teacher also checks other cases,
your report, figures, and explanation. Do not change supplied tests just to pass them.

In the notebook, restart the kernel and run all cells from top to bottom. A kernel
is the Python process running the notebook. Check that no earlier hidden state is needed.
Keep the original input files unchanged. Do not submit `.venv` or passwords/tokens.

## 4. Submit on GitHub

1. Use the teacher's template to create your own **private** repository. Make sure the teacher can access it. Use a student ID.
2. Create a branch named `submission`. Keep `main` as the starting version.
3. Commit your code, completed notebook, REPORT.md, AI_USE.md, extra tests, and required outputs.
4. Open a pull request from `submission` to `main`. Title: `Lab XX — STUDENT_ID`. Replace XX and STUDENT_ID with your lab number and course ID.
5. Do not merge before the teacher finishes assessment.
6. Submit the pull-request URL and full commit SHA in the university submission system. A commit SHA identifies one saved version. Use the SHA after your final push.
7. Follow the teacher's deadline. Later changes do not replace the recorded version unless the teacher accepts a new submission. Commit dates alone do not prove receipt.

## AI-use rule

AI help is allowed when the teacher's course policy allows it and you disclose it. You must check results and explain all submitted code. The teacher sets the final course policy and marks.
