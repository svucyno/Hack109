"""
JSON structured logging formatter.
SRS NFR-5.4: Emit structured logs with correlation_id fields.
"""

import json
import logging


class JSONFormatter(logging.Formatter):
    """Format log records as JSON with correlation context."""
    
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Include correlation_id if available in context
        if hasattr(record, 'correlation_id'):
            log_data['correlation_id'] = record.correlation_id
        
        # Include exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)
