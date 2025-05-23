# jobfit-ai-backend

This project is the backend for an AI Job Application Assistant. Its key capabilities include:

*   Resume tailoring
*   Job description analysis
*   HR question answering
*   Applicant Tracking System (ATS) checking

## Key Features

*   **resume_tailor**: Tailors resumes to specific job descriptions.
*   **jp_analyser**: Analyzes job descriptions to extract key skills and requirements.
*   **hr_qa_routes**: Answers HR-related questions based on provided documents.
*   **ats_checker_routes**: Checks resumes against Applicant Tracking System (ATS) criteria.

## Project Setup and Installation

This is a Python FastAPI project. To get started, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd jobfit-ai-backend
    ```

2.  **Create and activate a virtual environment (optional but recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    Dependencies are listed in `requirements.txt`. Install them using pip:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Environment variables are used for configuration, such as API keys. An example file `.env.example` is provided.
    *   Create a `.env` file by copying `.env.example`:
        ```bash
        cp .env.example .env
        ```
    *   Open the `.env` file and configure the following key variables:
        *   `GOOGLE_API_KEY`: Your Google API key.
        *   `SERPER_API_KEY`: Your Serper API key.
        *   `DEFAULT_LLM_PROVIDER`: The default LLM provider to use (e.g., `google` or `openai`).

5.  **Run the application:**
    Use the following command to start the development server with Uvicorn:
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```
    This command starts the FastAPI application on `http://0.0.0.0:8000`. The `--reload` flag enables auto-reloading when code changes are detected.

## API Endpoints

All API routes are prefixed with `/api`.

The main service routers available are:

*   `/resume-tailor/check`: Endpoints for tailoring resumes.
*   `/jp-analyser/analyze`: Endpoints for analyzing job descriptions.
*   `/hr-qa/answer`: Endpoints for HR-related question answering.
*   `/ats-checker/check`: Endpoints for checking resumes against ATS criteria.

For detailed endpoint definitions, please refer to the code within the `app/api/routes/` directory.

### Health Check

*   `/health`: Use this endpoint to check the application's status.

## Configuration

Core application settings are managed in the `app/core/config.py` file. These settings can be overridden by environment variables, such as those defined in your `.env` file.

For a detailed list of available configuration options and their default values, please refer to the `app/core/config.py` file.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contributing

We welcome contributions to enhance the jobfit-ai-backend! If you're interested in helping, here are some ways you can contribute:

*   **Reporting Bugs**: If you encounter any bugs or issues, please report them by opening an issue on the project's issue tracker.
*   **Suggesting Features**: Have an idea for a new feature or an improvement to an existing one? We'd love to hear it! Please open an issue to discuss your suggestion.
*   **Submitting Pull Requests**: If you've made improvements to the codebase, feel free to submit a pull request. Please ensure your code follows the project's coding standards and includes relevant tests.

All contributions are welcome and highly appreciated!
