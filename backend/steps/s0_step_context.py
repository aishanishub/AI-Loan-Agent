# loan_agent/backend/steps/s0_step_context.py

class SimpleContext:
    """A context object that uses a persistent, external state dictionary
    and collects events to be processed by the UI orchestrator.
    """
    def __init__(self, persistent_state: dict):
        # This 'state' is now a reference to an external dict
        # (e.g., st.session_state.step_work_state)
        self.state: dict = persistent_state
        self.emitted_events: list[dict] = []

    async def emit_event(self, event: dict):
        """Adds an event to the list for the UI to process."""
        self.emitted_events.append(event)