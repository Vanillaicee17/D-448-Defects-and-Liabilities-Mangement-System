from models.defect_history import DefectHistory


def log_history(db, defect_id, user_id, action, old_value=None, new_value=None):

    history = DefectHistory(
        defect_id=defect_id,
        changed_by=user_id,
        action=action,
        old_value=str(old_value),
        new_value=str(new_value)
    )

    db.add(history)
