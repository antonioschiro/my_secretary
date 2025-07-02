def build_query(
                recipients: None|str| list[str] = None,
                mail_subject: None|str = None,
                start_date: None|str = None,
                end_date: None|str = None,
                mail_state: None| str = None,
                folder: None| str = None,
                label: None| str = None,
                ) -> str:
    """
    Constructs a search query string for filtering emails based on various criteria.

    Parameters:
        recipients (None | str | list[str], optional): Email address or list of addresses to filter by sender.
        mail_subject (None | str, optional): Subject text to filter emails.
        start_date (None | str, optional): Start date (YYYY/MM/DD) to filter emails sent after this date.
        end_date (None | str, optional): End date (YYYY/MM/DD) to filter emails sent before this date.
        mail_state (None | str, optional): State of the email (e.g., 'read', 'unread').
        folder (None | str, optional): Folder to filter emails (e.g., 'inbox', 'sent').
        label (None | str, optional): Label to filter emails.

    Returns:
        str: A query string combining all provided filters, suitable for use in email search APIs.

    Raises:
        TypeError: If recipients is not a string or list of strings.

    Example:
        build_query(recipients=["alice@example.com", "bob@example.com"], mail_subject="Meeting", start_date="2024/01/01")
        # Returns: '(from:alice@example.com OR from:bob@example.com) subject:"Meeting" after:2024/01/01'
    """
    filters_list = []

    if recipients is not None:
        if isinstance(recipients, str):
            from_filter = f"from:{recipients}"
        elif isinstance(recipients, list):
            from_filter = ' OR '.join(f"from:{recipient}" for recipient in recipients)
            from_filter = f"({from_filter})"
        else:
            raise TypeError("Check recipients type.")
        filters_list.append(from_filter)

    if mail_subject is not None:
        subject_filter = f"subject:\"{mail_subject}\""
        filters_list.append(subject_filter)

    if mail_state is not None:
        state_filter = f"is:{mail_state}"
        filters_list.append(state_filter)

    if folder is not None:
        folder_filter = f"in:{folder}"
        filters_list.append(folder_filter)

    if start_date is not None:
        after_filter = f"after:{start_date}"
        filters_list.append(after_filter)
    
    if end_date is not None:
        before_filter = f"before:{end_date}"
        filters_list.append(before_filter)

    if label is not None:
        label_filter = f"label:{label}"
        filters_list.append(label_filter)
    
    return ' '.join(filter for filter in filters_list)