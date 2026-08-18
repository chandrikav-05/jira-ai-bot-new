import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY      = os.getenv("OPENAI_API_KEY")
JIRA_URL            = os.getenv("JIRA_URL")
JIRA_EMAIL          = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN      = os.getenv("JIRA_API_TOKEN")
DEFAULT_PROJECT_KEY = os.getenv("DEFAULT_PROJECT_KEY")


