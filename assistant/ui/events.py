# Minimal event bus for orb UI - provides BUS compatible interface
class _Bus:
    def emit(self, *args, **kwargs): 
        print(f"[BUS] emit {args} {kwargs}")
        return None
    def __getattr__(self, name):
        # any BUS.xxx returns self that can emit
        return self

BUS = _Bus()
# Also provide named signals for compatibility
BUS.listening_started = _Bus()
BUS.speaking_started = _Bus()
BUS.task_completed = _Bus()
BUS.task_failed = _Bus()
BUS.task_cancelled = _Bus()
