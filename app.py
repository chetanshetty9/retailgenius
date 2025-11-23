import streamlit as st
import time
from main import analyze_single_review
from src.features.load_dataset import load_dataset
from src.features.prompt_injection import human_in_loop_decision
from src.features.jira_ticket import create_jira_ticket  # import here for direct call

st.set_page_config(page_title="AI Review Analyzer", layout="wide")
st.title("📊 Customer Review Analysis Dashboard")

# -----------------------------
# Tab selection: Single vs Batch
# -----------------------------
tab = st.radio("Choose mode:", ["Single Review", "Batch Reviews"])

# -----------------------------
# Single Review Mode
# -----------------------------
# -----------------------------
# Single Review Mode
# -----------------------------
# -----------------------------
# Single Review Mode
# -----------------------------
if tab == "Single Review":
    review_text = st.text_area("Enter a customer review:", height=180)

    # Initialize session state for Single Review
    if "single_result" not in st.session_state:
        st.session_state.single_result = None
    if "single_next_clicked" not in st.session_state:
        st.session_state.single_next_clicked = False
    if "human_choice_single" not in st.session_state:
        st.session_state.human_choice_single = "Generate AI Response"

    # Analyze review when button clicked
    if st.button("Analyze Review") and review_text.strip():
        st.session_state.single_result = analyze_single_review(review_text)
        st.session_state.single_next_clicked = False

    result = st.session_state.single_result

    if result:
        # Display review info
        st.markdown(f"### 📝 Review 1")
        st.write("**Original Review:**", result.get("review"))
        st.write("**Clean Text:**", result.get("clean_text"))
        st.write("**Safe Text:**", result.get("safetext"))
        st.write("**Warning:**", result.get("warning"))
        st.write("**Critical Ref Number:**", result.get("critical_ref_num"))
        st.write("**Sentiment:**", result.get("sentiment"))
        st.write("**Key Issues:**", result.get("key_issues"))
        st.write("**Summary:**", result.get("summary"))
        st.write("**Language:**", result.get("lang"))
        st.write("**Mode:**", result.get("mode"))

        # Human-in-the-loop for critical reviews
        # Human-in-the-loop for critical reviews
        if result.get("warning") == "yes" and result.get("critical_ref_num"):
            # Radio button for choice
            st.session_state.human_choice_single = st.radio(
                "Create JIRA Ticket or Generate AI Response?",
                ("Generate AI Response","Create JIRA Ticket"),
                index=0 if st.session_state.human_choice_single == "Generate AI Response" else 1,
                key="human_single"
            )

            # Proceed button
            if st.button("Proceed") and not st.session_state.single_next_clicked:
                # --- Place the fixed mapping code here ---
                choice = st.session_state.human_choice_single.strip().lower()
                result["human_decision"] = "yes" if choice == "create jira ticket" else "no"
                next_step = human_in_loop_decision(result)

                # Execute JIRA or AI response
                if next_step == "create_jira_ticket":
                    result = create_jira_ticket(result)
                    st.success(f"✅ JIRA ticket created")
                elif next_step == "generate_response":
                    st.subheader("💬 AI Response")
                    st.info(result.get("customer_response"))

                st.session_state.single_next_clicked = True


        else:
            # Normal review: show AI response
            st.subheader("💬 AI Response")
            st.info(result.get("customer_response"))
            st.session_state.single_next_clicked = True

# -----------------------------
# Batch Review Mode
# -----------------------------
else:
    # Initialize session state
    if "review_index" not in st.session_state:
        st.session_state.review_index = 0
    if "results" not in st.session_state:
        st.session_state.results = []
    if "next_clicked" not in st.session_state:
        st.session_state.next_clicked = False

    data = load_dataset()
    reviews = data.get("reviews", [])
    total_reviews = len(reviews)

    if total_reviews == 0:
        st.warning("No reviews found in the dataset.")
    else:
        # Display current review
        if st.session_state.review_index < total_reviews:
            i = st.session_state.review_index
            review = reviews[i]
            result = analyze_single_review(review.get("review_text", ""))

            st.markdown(f"### 📝 Review {i + 1}")
            st.write("**Original Review:**", result.get("review"))
            st.write("**Clean Text:**", result.get("clean_text"))
            st.write("**Safe Text:**", result.get("safetext"))
            st.write("**Warning:**", result.get("warning"))
            st.write("**Critical Ref Number:**", result.get("critical_ref_num"))
            st.write("**Sentiment:**", result.get("sentiment"))
            st.write("**Key Issues:**", result.get("key_issues"))
            st.write("**Summary:**", result.get("summary"))
            st.write("**Language:**", result.get("lang"))
            st.write("**Mode:**", result.get("mode"))

            # -----------------------------
            # Human-in-the-loop for critical reviews
            # -----------------------------
            next_step = None
            if result.get("warning") == "yes" and result.get("critical_ref_num"):
                human_choice = st.radio(
                    "Create JIRA Ticket or Generate AI Response?",
                    ("Create JIRA Ticket", "Generate AI Response"),
                    key=f"human_{i}"
                )

                if st.button("Proceed") and not st.session_state.next_clicked:
                    result["human_decision"] = (
                        "yes" if human_choice == "Create JIRA Ticket" else "no"
                    )
                    next_step = human_in_loop_decision(result)
                    st.session_state.results.append((result, next_step))
                    st.session_state.next_clicked = True

                    # Execute JIRA or show AI response
                    if next_step == "create_jira_ticket":
                        create_jira_ticket(result)
                        st.write("**Ticket:**", result.get("jira_ticket"))
                    else:
                        st.subheader("💬 AI Response")
                        st.info(result.get("customer_response"))

            else:
                # Normal review: show AI response
                st.subheader("💬 Customer Response")
                st.info(result.get("customer_response"))
                next_step = "generate_response"
                st.session_state.next_clicked = True

            # -----------------------------
            # Show Next Review button
            # -----------------------------
            if st.session_state.next_clicked:
                if st.button("Next Review"):
                    st.session_state.review_index += 1
                    st.session_state.next_clicked = False

                    # Optional 15-second wait before next review
                    if st.session_state.review_index < total_reviews:
                        st.write("⏳ Waiting 1 second before next review...")
                        time.sleep(1)

        else:
            st.success("🎉 All reviews processed!")
            st.write("Processed Results:")
            for idx, (res, step) in enumerate(st.session_state.results, start=1):
                st.markdown(f"**Review {idx}: {step}**")
                st.write("Original:", res.get("review"))
                st.write("Customer Response:", res.get("customer_response"))
