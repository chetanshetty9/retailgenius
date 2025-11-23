import os
from jira import JIRA
from dotenv import load_dotenv

load_dotenv()  # Loads .env variables

def create_jira_ticket(state):
    """
    Creates a Jira ticket for a critical customer review.

    This step is triggered only if a critical reference number (CRITICAL_REF)
    is present in the pipeline state. The function connects to Jira using API
    credentials, constructs a ticket summarizing the sanitized customer
    review, sentiment, key issues, and summary, and submits it to the
    configured Jira project.

    The created Jira issue key is added back into the state under
    `state["jira_ticket"]`. If applicable, it can also be appended to the
    customer-facing response.

    Args:
        state (dict): The LangGraph state containing review details and the
                      generated `critical_ref_num`.

    Returns:
        dict: Updated state including the created Jira ticket key.
    """
    print("We are inside create jira ticket")
    critical_ref = state.get("critical_ref_num")

    if critical_ref:
        jira_options = {"server": "https://chetanshetty1986.atlassian.net/"}
        jira = JIRA(
            options=jira_options,
            basic_auth=(
            os.getenv("JIRA_EMAIL"),
            os.getenv("JIRA_API_TOKEN"),
        ),
        )

        summary = f"Critical Customer Review: {critical_ref}"

        description = (
            f"Sanitized review:\n{state.get('safetext')}\n\n"
            f"Sentiment: {state.get('sentiment')}\n"
            f"Key issues: {state.get('key_issues')}\n"
            f"Summary: {state.get('summary')}"
        )

        issue_dict = {
            "project": {"key": "KAN"},
            "summary": summary,
            "description": description,
            "issuetype": {"name": "Task"},
        }

        jira_issue = jira.create_issue(fields=issue_dict)
        print('jira_issue:',jira_issue)
        state["jira_ticket"] = jira_issue.key

        # Optionally append Jira link to customer response
        if "output" in state and "customer_response" in state["output"]:
            state["output"]["customer_response"] += f" [Jira Ticket: {jira_issue.key}]"
        else:
            state["jira_ticket"] = None

        return state


def check_critical_condition(state):
    """
    Determines the next step in the pipeline based on critical review logic.

    Logic:
    - If a critical reference number exists:
        - If unsafe content or prompt injection was detected (`warning == "yes"`),
          route execution to the `human_in_loop` review step.
        - Otherwise, proceed directly to Jira ticket creation.
    - If no critical reference exists, route execution to the standard
      customer response generator.

    This function is used as the conditional router inside LangGraph.

    Args:
        state (dict): Current pipeline state.

    Returns:
        str: Name of the next node ("human_in_loop", "create_jira_ticket",
             or "generate_response").
    """
    
    if state["critical_ref_num"]:
        if state["warning"] == "yes":
            return "human_in_loop"
        else:
            return "create_jira_ticket"
    else:
        return "generate_response"
