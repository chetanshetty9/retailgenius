def human_in_loop(state):
    """
    Triggers a human review step when a critical reference or unsafe content is detected.
    Captures the human's decision to proceed with Jira ticket creation.
    """
    warning = state["warning"]
    critical_ref = state["critical_ref_num"]

    # Human approval is required for critical or unsafe reviews
    if (warning == "yes") or (critical_ref):
        print(
            "\nAlert: Potential prompt injection detected in a critical review. Human review is required."
        )

        # Overridden input() always returns "yes" unless modified
        decision = (
            input("Would you like to proceed with creating a JIRA ticket? (yes/no):")
            .strip()
            .lower()
        )

        if decision == "yes":
            state["human_decision"] = decision
        else:
            print("Mitigating prompt injection and generating a safe response")
            state["human_decision"] = "no"
    return state



def human_in_loop_decision(state):
    """
    Routes the workflow based on the human decision:
    'yes' → create Jira ticket, 'no' → generate a safe customer response.
    """
    if state["human_decision"] == "yes":
        return "create_jira_ticket"
    else:
        return "generate_response"
