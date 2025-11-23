def human_in_loop(state):
    """
    Triggers human review step for critical or unsafe content.
    For Streamlit UI, the human decision should be set externally via state["human_decision"].
    """
    warning = state.get("warning")
    critical_ref = state.get("critical_ref_num")

    # Only trigger human review if critical or unsafe
    if warning == "yes" or critical_ref:
        # Assume human_decision is already set from UI
        if "human_decision" not in state or state["human_decision"] is None:
            # Optional fallback for CLI mode, or set default
            state["human_decision"] = "no"
    else:
        state["human_decision"] = "no"

    return state


def human_in_loop_decision(state):
    """
    Routes the workflow based on the human decision:
    'yes' → create Jira ticket, 'no' → generate a safe customer response.
    """
    if state["human_decision"] == "yes":
        print('Going to create jira ticket')
        return "create_jira_ticket"
    else:
        return "generate_response"
