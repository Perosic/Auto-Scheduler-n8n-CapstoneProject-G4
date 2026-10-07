"""
Email delivery for the generated timetable.

Streamlit -> n8n "Gmail Timetable Sender" workflow -> Gmail

The Gmail workflow lives in n8n/Gmail_Timetable_Sender.json and is
documented in docs/integrations/GMAIL_N8N_INTEGRATION.md.
This module only calls its webhook; it does not change the
scheduling workflow.
"""

import os
import re

import requests
import streamlit as st


# ============================================================
# N8N GMAIL WEBHOOK
# ============================================================

# Can be overridden with the N8N_SEND_SCHEDULE_URL environment variable.
N8N_SEND_SCHEDULE_URL = os.getenv(
    "N8N_SEND_SCHEDULE_URL",
    "http://localhost:5678/webhook/send-schedule",
)

EMAIL_TIMEOUT_SECONDS = 60

DEFAULT_SUBJECT = "Your Course Timetable"

EMAIL_PATTERN = re.compile(
    r"^[^\s@,;]+@[^\s@,;]+\.[^\s@,;]+$"
)

# Fields the Gmail workflow uses for each class.
# "lecturer" is the scheduler's name for the instructor (database term).
EMAIL_FIELDS = ("course", "title", "lecturer", "day", "time", "room")


def split_recipients(raw_value):
    """
    Turn "a@x.com, b@y.com" into a clean list of addresses.
    """

    return [
        address.strip()
        for address in str(raw_value or "").split(",")
        if address.strip()
    ]


def invalid_recipients(addresses):
    """
    Return the addresses that do not look like email addresses.
    """

    return [
        address
        for address in addresses
        if not EMAIL_PATTERN.match(address)
    ]


def build_schedule_payload(placed):
    """
    Keep only the fields the email needs, in the shape the
    Gmail workflow expects. Day and time are sent exactly as the
    scheduler returns them; the workflow formats them.
    """

    schedule = []

    for item in placed or []:

        entry = {
            field: item.get(field)
            for field in EMAIL_FIELDS
        }

        if not entry.get("course"):
            entry["course"] = (
                item.get("code")
                or item.get("course_code")
            )

        schedule.append(entry)

    return schedule


def send_timetable_email(
    recipients,
    subject,
    placed,
    url=None,
    timeout=EMAIL_TIMEOUT_SECONDS,
):
    """
    Send the timetable to the n8n Gmail workflow.

    Always returns a dict with at least "success" and "message".
    Never raises, so the page cannot crash on a failed send.
    """

    payload = {
        "recipient": ", ".join(recipients),
        "subject": (subject or "").strip() or DEFAULT_SUBJECT,
        "schedule": build_schedule_payload(placed),
    }

    try:

        response = requests.post(
            url or N8N_SEND_SCHEDULE_URL,
            json=payload,
            timeout=timeout,
        )

    except requests.exceptions.Timeout:

        return {
            "success": False,
            "message": "n8n took too long to respond while sending the email.",
        }

    except requests.exceptions.ConnectionError:

        return {
            "success": False,
            "message": (
                "Could not connect to n8n. Make sure n8n is running "
                "at http://localhost:5678."
            ),
        }

    try:

        data = response.json()

    except ValueError:

        data = {}

    if response.status_code == 404:

        return {
            "success": False,
            "message": (
                "The Gmail workflow was not found in n8n. Import "
                "n8n/Gmail_Timetable_Sender.json, connect your Gmail "
                "credential and publish it."
            ),
        }

    if not isinstance(data, dict) or "success" not in data:

        return {
            "success": False,
            "message": (
                f"Unexpected response from n8n (HTTP {response.status_code})."
            ),
            "details": response.text[:500],
        }

    return data


def render_email_section(placed):
    """
    Show the "Send timetable by email" form under the timetable.
    """

    st.subheader("📧 Send Timetable by Email")

    if not placed:

        st.info(
            "There are no placed courses to email yet."
        )

        return

    st.caption(
        f"Sends the full timetable ({len(placed)} classes) through "
        "the n8n Gmail workflow. Separate several addresses with commas."
    )

    with st.form(
        "email_timetable_form",
        clear_on_submit=False,
    ):

        recipient_input = st.text_input(
            "Recipient email",
            placeholder="student@example.com",
        )

        subject_input = st.text_input(
            "Subject",
            value=DEFAULT_SUBJECT,
        )

        send_clicked = st.form_submit_button(
            "📧 Send Timetable",
            use_container_width=True,
        )

    if not send_clicked:

        return

    recipients = split_recipients(recipient_input)

    if not recipients:

        st.error(
            "Please enter at least one email address."
        )

        return

    bad_addresses = invalid_recipients(recipients)

    if bad_addresses:

        st.error(
            "These don't look like email addresses: "
            + ", ".join(bad_addresses)
        )

        return

    with st.spinner(
        "Sending the timetable through n8n and Gmail..."
    ):

        outcome = send_timetable_email(
            recipients,
            subject_input,
            placed,
        )

    if outcome.get("success"):

        st.success(
            f"✅ Timetable sent to {', '.join(recipients)}."
        )

        return

    st.error(
        f"❌ {outcome.get('message', 'The email could not be sent.')}"
    )

    for error in outcome.get("errors", []):

        st.warning(str(error))

    if outcome.get("error"):

        st.warning(str(outcome["error"]))

    if outcome.get("details"):

        st.code(outcome["details"])
