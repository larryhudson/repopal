"""Core module exceptions"""

class CoreError(Exception):
    """Base class for core module errors"""
    pass

class PipelineError(CoreError):
    """Base class for pipeline-related errors"""
    pass

class PipelineNotFoundError(PipelineError):
    """Raised when a pipeline cannot be found"""
    def __init__(self, pipeline_id: str):
        self.pipeline_id = pipeline_id
        super().__init__(f"Pipeline not found: {pipeline_id}")

class PipelineStateError(PipelineError):
    """Raised when an invalid pipeline state transition is attempted"""
    pass

class ServiceConnectionError(CoreError):
    """Raised when there are issues with service connections"""
    pass
