"""
Batch Processor Module
Batch operations for documents and searches

Features:
- Batch search
- Batch export
- Batch tagging
- Batch deletion
- Progress tracking
- Error handling
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class BatchOperationType(Enum):
    """Batch operation type"""

    SEARCH = "search"
    EXPORT = "export"
    TAG = "tag"
    DELETE = "delete"
    PROCESS = "process"


@dataclass
class BatchOperation:
    """Batch operation

    Attributes:
        id: Operation ID
        type: Operation type
        items: Items to process
        parameters: Operation parameters
        status: Operation status
        progress: Progress percentage
        results: Operation results
        errors: Operation errors
    """

    id: str
    type: BatchOperationType
    items: List[Dict[str, Any]]
    parameters: Dict[str, Any]
    status: str = "pending"
    progress: float = 0.0
    results: List[Dict[str, Any]] = None
    errors: List[str] = None

    def __post_init__(self):
        """Post-init initialization"""
        if self.results is None:
            self.results = []
        if self.errors is None:
            self.errors = []


@dataclass
class BatchResult:
    """Batch operation result

    Attributes:
        operation_id: Operation ID
        success: Overall success
        total_items: Total items processed
        successful_items: Successfully processed items
        failed_items: Failed items
        results: Operation results
        errors: Operation errors
        duration_ms: Operation duration
    """

    operation_id: str
    success: bool
    total_items: int
    successful_items: int
    failed_items: int
    results: List[Dict[str, Any]]
    errors: List[str]
    duration_ms: float


class BatchProcessor:
    """Process batch operations"""

    def __init__(self):
        """Initialize batch processor"""
        self.operations: Dict[str, BatchOperation] = {}
        self.handlers: Dict[BatchOperationType, Callable] = {}
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default handlers"""
        self.handlers[BatchOperationType.SEARCH] = self._handle_search
        self.handlers[BatchOperationType.EXPORT] = self._handle_export
        self.handlers[BatchOperationType.TAG] = self._handle_tag
        self.handlers[BatchOperationType.DELETE] = self._handle_delete
        self.handlers[BatchOperationType.PROCESS] = self._handle_process

    def register_handler(
        self, operation_type: BatchOperationType, handler: Callable
    ) -> None:
        """Register operation handler

        Args:
            operation_type: Operation type
            handler: Handler function
        """
        self.handlers[operation_type] = handler
        logger.info(f"Registered handler for: {operation_type.value}")

    def create_operation(
        self,
        operation_type: BatchOperationType,
        items: List[Dict[str, Any]],
        parameters: Optional[Dict[str, Any]] = None,
    ) -> BatchOperation:
        """Create batch operation

        Args:
            operation_type: Operation type
            items: Items to process
            parameters: Operation parameters

        Returns:
            Created operation
        """
        operation_id = self._generate_id()
        operation = BatchOperation(
            id=operation_id,
            type=operation_type,
            items=items,
            parameters=parameters or {},
        )
        self.operations[operation_id] = operation
        logger.info(f"Created batch operation: {operation_id}")
        return operation

    def execute(self, operation_id: str) -> BatchResult:
        """Execute batch operation

        Args:
            operation_id: Operation ID

        Returns:
            BatchResult
        """
        import time

        start_time = time.time()
        operation = self.operations.get(operation_id)

        if not operation:
            return BatchResult(
                operation_id=operation_id,
                success=False,
                total_items=0,
                successful_items=0,
                failed_items=0,
                results=[],
                errors=["Operation not found"],
                duration_ms=(time.time() - start_time) * 1000,
            )

        try:
            operation.status = "running"

            handler = self.handlers.get(operation.type)
            if not handler:
                operation.status = "failed"
                operation.errors.append(
                    f"Handler not found for: {operation.type.value}"
                )
                return self._create_result(operation, start_time)

            # Execute handler
            handler(operation)

            operation.status = "completed"

        except Exception as e:
            logger.error(f"Batch operation error: {e}")
            operation.status = "failed"
            operation.errors.append(str(e))

        return self._create_result(operation, start_time)

    def get_operation(self, operation_id: str) -> Optional[BatchOperation]:
        """Get operation by ID

        Args:
            operation_id: Operation ID

        Returns:
            BatchOperation or None
        """
        return self.operations.get(operation_id)

    def list_operations(self) -> List[BatchOperation]:
        """List all operations

        Returns:
            List of operations
        """
        return list(self.operations.values())

    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel operation

        Args:
            operation_id: Operation ID

        Returns:
            True if cancelled, False if not found
        """
        operation = self.operations.get(operation_id)
        if operation and operation.status == "running":
            operation.status = "cancelled"
            logger.info(f"Cancelled operation: {operation_id}")
            return True
        return False

    def _handle_search(self, operation: BatchOperation) -> None:
        """Handle batch search

        Args:
            operation: Batch operation
        """
        total = len(operation.items)
        for i, item in enumerate(operation.items):
            try:
                # Simulate search
                result = {
                    "item_id": item.get("id"),
                    "query": item.get("query"),
                    "results_count": 0,
                }
                operation.results.append(result)
                operation.progress = ((i + 1) / total) * 100
            except Exception as e:
                operation.errors.append(f"Search failed for item {i}: {str(e)}")

    def _handle_export(self, operation: BatchOperation) -> None:
        """Handle batch export

        Args:
            operation: Batch operation
        """
        total = len(operation.items)
        for i, item in enumerate(operation.items):
            try:
                # Simulate export
                result = {
                    "item_id": item.get("id"),
                    "format": operation.parameters.get("format", "json"),
                    "exported": True,
                }
                operation.results.append(result)
                operation.progress = ((i + 1) / total) * 100
            except Exception as e:
                operation.errors.append(f"Export failed for item {i}: {str(e)}")

    def _handle_tag(self, operation: BatchOperation) -> None:
        """Handle batch tagging

        Args:
            operation: Batch operation
        """
        total = len(operation.items)
        tags = operation.parameters.get("tags", [])
        for i, item in enumerate(operation.items):
            try:
                # Simulate tagging
                result = {
                    "item_id": item.get("id"),
                    "tags_added": tags,
                    "tagged": True,
                }
                operation.results.append(result)
                operation.progress = ((i + 1) / total) * 100
            except Exception as e:
                operation.errors.append(f"Tagging failed for item {i}: {str(e)}")

    def _handle_delete(self, operation: BatchOperation) -> None:
        """Handle batch deletion

        Args:
            operation: Batch operation
        """
        total = len(operation.items)
        for i, item in enumerate(operation.items):
            try:
                # Simulate deletion
                result = {
                    "item_id": item.get("id"),
                    "deleted": True,
                }
                operation.results.append(result)
                operation.progress = ((i + 1) / total) * 100
            except Exception as e:
                operation.errors.append(f"Deletion failed for item {i}: {str(e)}")

    def _handle_process(self, operation: BatchOperation) -> None:
        """Handle batch processing

        Args:
            operation: Batch operation
        """
        total = len(operation.items)
        processor = operation.parameters.get("processor")
        for i, item in enumerate(operation.items):
            try:
                if processor and callable(processor):
                    result = processor(item)
                else:
                    result = {"item_id": item.get("id"), "processed": True}
                operation.results.append(result)
                operation.progress = ((i + 1) / total) * 100
            except Exception as e:
                operation.errors.append(f"Processing failed for item {i}: {str(e)}")

    def _create_result(self, operation: BatchOperation, start_time: float) -> BatchResult:
        """Create batch result

        Args:
            operation: Batch operation
            start_time: Operation start time

        Returns:
            BatchResult
        """
        import time

        successful = len(operation.results)
        failed = len(operation.errors)
        total = len(operation.items)

        return BatchResult(
            operation_id=operation.id,
            success=operation.status == "completed" and failed == 0,
            total_items=total,
            successful_items=successful,
            failed_items=failed,
            results=operation.results,
            errors=operation.errors,
            duration_ms=(time.time() - start_time) * 1000,
        )

    def _generate_id(self) -> str:
        """Generate unique operation ID

        Returns:
            Unique ID
        """
        import uuid

        return str(uuid.uuid4())[:8]


def batch_search(
    queries: List[str], processor: Callable
) -> BatchResult:
    """Convenience function for batch search

    Args:
        queries: List of search queries
        processor: Query processor function

    Returns:
        BatchResult
    """
    batch_processor = BatchProcessor()
    items = [{"id": str(i), "query": q} for i, q in enumerate(queries)]
    operation = batch_processor.create_operation(
        BatchOperationType.SEARCH, items
    )
    return batch_processor.execute(operation.id)


def batch_export(
    items: List[Dict[str, Any]], format: str
) -> BatchResult:
    """Convenience function for batch export

    Args:
        items: Items to export
        format: Export format

    Returns:
        BatchResult
    """
    batch_processor = BatchProcessor()
    operation = batch_processor.create_operation(
        BatchOperationType.EXPORT,
        items,
        {"format": format},
    )
    return batch_processor.execute(operation.id)
