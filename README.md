# durable-execution-engine-SDK-python

## Introduction

This SDK provides a Python interface for building workflows that leverage the [Durable Execution Engine](https://github.com/SalmaElsoly/durable-execution-engine). The SDK is designed to help you build reliable, fault-tolerant workflows that can recover from failures and ensure consistent results.

### How It Works
- The SDK acts as a client that communicates with the Durable Execution Engine via HTTP API calls.
- When you execute workflow actions using the SDK, it logs action states (started, completed, failed) to the engine.
- The engine manages retries, result caching, and ensures that each action is executed exactly once, even in the face of failures or restarts.
- The SDK requires the `DURABLE_ENGINE_BASE_URL` environment variable to be set to the engine's API endpoint so it can send these logs and receive execution instructions.

For more details about the engine, see the [Durable Execution Engine repository](https://github.com/SalmaElsoly/durable-execution-engine).

**Full documentation and usage slides:**  [SDK & Engine Documentation Slides](https://engasuedu-my.sharepoint.com/:p:/g/personal/20p1269_eng_asu_edu_eg/Eb9egU5kUJNOpzjf4mINZh4BF_T3IQjr50G8RV868DNNUw?e=L5F8R8)

---

## Windows Setup Instructions

### 1. Install Python (version 3.10 or higher)
- Download from: https://www.python.org/downloads/
- During installation, **check the box** that says "Add Python to PATH".

### 2. Add Python and Scripts to Environment Variables
If you missed the "Add to PATH" step, add these folders to your user `PATH`:
- Example paths (adjust for your version/username):
  - `C:\Users\<YourUser>\AppData\Local\Programs\Python\Python310\`
  - `C:\Users\<YourUser>\AppData\Local\Programs\Python\Python310\Scripts\`

How to add:
- Open Start Menu → search "Environment Variables" → Edit environment variables for your account.
- Edit the `Path` variable and add the above folders.

### 3. If you see this error:
> Python was not found; run without arguments to install from the Microsoft Store, or disable this shortcut from Settings > Apps > Advanced app settings > App execution aliases.
- Make sure Python is installed and the correct folders are in your `PATH` (see above).
- You may need to disable the Microsoft Store Python alias in Windows settings.

### 4. Install Poetry
- Open PowerShell and run:
  ```powershell
  py -m pip install poetry
  ```
  or
  ```powershell
  (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
  ```
- Official docs: https://python-poetry.org/docs/#system-requirements

### 5. Add Poetry to your PATH
If `poetry` is not recognized, add its Scripts folder to your `PATH`:

**Option A: One-time append to user PATH**
```powershell
[Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path", "User") + ";C:\Users\<YourUser>\AppData\Roaming\Python\Scripts", "User")
```
Replace `<YourUser>` with your Windows username.

**Option B: Always append in PowerShell profile**
```powershell
echo 'if (-not (Get-Command poetry -ErrorAction Ignore)) { $env:Path += ";C:\Users\<YourUser>\AppData\Roaming\Python\Scripts" }' | Out-File -Append $PROFILE
```

### 6. Install Project Dependencies
- In your project directory, run:
  ```powershell
  poetry install
  ```

---

## Running the Example Folder

This example demonstrates how to use the SDK in practice, showcasing integration with an existing system (Food Delivery System, ...). Follow these steps to run the example with an existing engine instance:

> **Note:** The Durable Execution Engine must be running and accessible at the URL you set in `DURABLE_ENGINE_BASE_URL` before running the example.

1. **Set the DURABLE_ENGINE_BASE_URL environment variable**

   This variable **must** be set or the project will not run.

   In PowerShell (Windows):
   ```powershell
   $env:DURABLE_ENGINE_BASE_URL="http://localhost:8080/api/v1"
   ```
   Adjust the URL if your engine is running elsewhere.

2. **Navigate to the example folder:**
   ```powershell
   cd example
   ```

3. **Run the example:**
   ```powershell
   poetry run python main.py
   ```

---

## Notes
- Make sure the durable execution engine is running and accessible at the URL you set in `DURABLE_ENGINE_BASE_URL`.
- If you are running the engine in Docker, you may need to adjust the URL (see Docker networking documentation).
- The project will not function without the `DURABLE_ENGINE_BASE_URL` environment variable set.