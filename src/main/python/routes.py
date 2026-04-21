"""
Main routes module for the Project application.
Handles HTTP request routing and response generation.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, Response
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError

# Configure logging
logger = logging.getLogger(__name__)

# Create main blueprint
main_bp = Blueprint('main', __name__)


@main_bp.route('/health', methods=['GET'])
def health_check() -> Response:
    """
    Health check endpoint to verify service is running.
    
    Returns:
        JSON response with service status and timestamp
    """
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'Project',
            'version': current_app.config.get('VERSION', '1.0.0')
        }
        logger.info('Health check completed successfully')
        return jsonify(health_status), 200
    except Exception as e:
        logger.error(f'Health check failed: {str(e)}')
        return jsonify({'error': 'Health check failed'}), 500


@main_bp.route('/api/data', methods=['GET'])
def get_data() -> Response:
    """
    Retrieve data from the service.
    
    Query Parameters:
        limit (int): Maximum number of items to return (default: 10)
        offset (int): Number of items to skip (default: 0)
    
    Returns:
        JSON response containing data items
    """
    try:
        # Extract query parameters with defaults
        limit = request.args.get('limit', default=10, type=int)
        offset = request.args.get('offset', default=0, type=int)
        
        # Validate parameters
        if limit < 1 or limit > 100:
            raise BadRequest('Limit must be between 1 and 100')
        if offset < 0:
            raise BadRequest('Offset must be non-negative')
        
        # In a real application, this would query a database or external service
        # For demonstration, return mock data
        mock_data = [
            {
                'id': i,
                'name': f'Item {i}',
                'created_at': datetime.utcnow().isoformat()
            }
            for i in range(offset, offset + min(limit, 10))
        ]
        
        response_data = {
            'data': mock_data,
            'metadata': {
                'limit': limit,
                'offset': offset,
                'total': len(mock_data),
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        logger.info(f'Retrieved {len(mock_data)} data items')
        return jsonify(response_data), 200
        
    except BadRequest as e:
        logger.warning(f'Bad request in get_data: {str(e)}')
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f'Error in get_data: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@main_bp.route('/api/data/<int:item_id>', methods=['GET'])
def get_data_item(item_id: int) -> Response:
    """
    Retrieve a specific data item by ID.
    
    Args:
        item_id: Unique identifier of the data item
    
    Returns:
        JSON response containing the requested data item
    """
    try:
        # Validate item_id
        if item_id <= 0:
            raise BadRequest('Item ID must be positive')
        
        # In a real application, this would query a database
        # For demonstration, return mock data if ID exists
        if item_id > 100:
            raise NotFound(f'Item with ID {item_id} not found')
        
        item_data = {
            'id': item_id,
            'name': f'Item {item_id}',
            'description': f'Description for item {item_id}',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f'Retrieved data item with ID: {item_id}')
        return jsonify(item_data), 200
        
    except BadRequest as e:
        logger.warning(f'Bad request in get_data_item: {str(e)}')
        return jsonify({'error': str(e)}), 400
    except NotFound as e:
        logger.warning(f'Item not found in get_data_item: {str(e)}')
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f'Error in get_data_item: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@main_bp.route('/api/data', methods=['POST'])
def create_data_item() -> Response:
    """
    Create a new data item.
    
    Request Body (JSON):
        name (str): Name of the item (required)
        description (str): Description of the item (optional)
    
    Returns:
        JSON response containing the created data item
    """
    try:
        # Parse and validate request data
        if not request.is_json:
            raise BadRequest('Request must be JSON')
        
        data: Dict[str, Any] = request.get_json()
        
        # Validate required fields
        if 'name' not in data or not data['name'].strip():
            raise BadRequest('Name is required')
        
        name = data['name'].strip()
        description = data.get('description', '').strip()
        
        # Validate field lengths
        if len(name) > 100:
            raise BadRequest('Name must be 100 characters or less')
        if len(description) > 500:
            raise BadRequest('Description must be 500 characters or less')
        
        # In a real application, this would save to a database
        # For demonstration, generate a mock ID
        new_item_id = 101  # This would come from database insert
        
        created_item = {
            'id': new_item_id,
            'name': name,
            'description': description,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f'Created new data item with ID: {new_item_id}')
        return jsonify(created_item), 201
        
    except BadRequest as e:
        logger.warning(f'Bad request in create_data_item: {str(e)}')
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f'Error in create_data_item: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@main_bp.route('/api/data/<int:item_id>', methods=['PUT'])
def update_data_item(item_id: int) -> Response:
    """
    Update an existing data item.
    
    Args:
        item_id: Unique identifier of the data item to update
    
    Request Body (JSON):
        name (str): Updated name (optional)
        description (str): Updated description (optional)
    
    Returns:
        JSON response containing the updated data item
    """
    try:
        # Validate item_id
        if item_id <= 0:
            raise BadRequest('Item ID must be positive')
        
        # Parse and validate request data
        if not request.is_json:
            raise BadRequest('Request must be JSON')
        
        data: Dict[str, Any] = request.get_json()
        
        # Check if item exists (in real app, query database)
        if item_id > 100:
            raise NotFound(f'Item with ID {item_id} not found')
        
        # Validate fields if provided
        if 'name' in data:
            name = data['name'].strip()
            if not name:
                raise BadRequest('Name cannot be empty')
            if len(name) > 100:
                raise BadRequest('Name must be 100 characters or less')
        
        if 'description' in data:
            description = data['description'].strip()
            if len(description) > 500:
                raise BadRequest('Description must be 500 characters or less')
        
        # In a real application, this would update the database
        # For demonstration, return updated mock data
        updated_item = {
            'id': item_id,
            'name': data.get('name', f'Item {item_id}'),
            'description': data.get('description', f'Updated description for item {item_id}'),
            'created_at': datetime.utcnow().isoformat(),  # Would come from DB
            'updated_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f'Updated data item with ID: {item_id}')
        return jsonify(updated_item), 200
        
    except BadRequest as e:
        logger.warning(f'Bad request in update_data_item: {str(e)}')
        return jsonify({'error': str(e)}), 400
    except NotFound as e:
        logger.warning(f'Item not found in update_data_item: {str(e)}')
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f'Error in update_data_item: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@main_bp.route('/api/data/<int:item_id>', methods=['DELETE'])
def delete_data_item(item_id: int) -> Response:
    """
    Delete a data item by ID.
    
    Args:
        item_id: Unique identifier of the data item to delete
    
    Returns:
        Empty response with 204 status on success
    """
    try:
        # Validate item_id
        if item_id <= 0:
            raise BadRequest('Item ID must be positive')
        
        # Check if item exists (in real app, query database)
        if item_id > 100:
            raise NotFound(f'Item with ID {item_id} not found')
        
        # In a real application, this would delete from database
        logger.info(f'Deleted data item with ID: {item_id}')
        return '', 204
        
    except BadRequest as e:
        logger.warning(f'Bad request in delete_data_item: {str(e)}')
        return jsonify({'error': str(e)}), 400
    except NotFound as e:
        logger.warning(f'Item not found in delete_data_item: {str(e)}')
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f'Error in delete_data_item: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@main_bp.errorhandler(404)
def not_found_error(error) -> Response:
    """
    Handle 404 errors for undefined routes.
    
    Args:
        error: The error that occurred
    
    Returns:
        JSON response with error details
    """
    logger.warning(f'Route not found: {request.path}')
    return jsonify({
        'error': 'Route not found',
        'path': request.path,
        'method': request.method
    }), 404


@main_bp.errorhandler(405)
def method_not_allowed_error(error) -> Response:
    """
    Handle 405 errors for unsupported HTTP methods.
    
    Args:
        error: The error that occurred
    
    Returns:
        JSON response with error details
    """
    logger.warning(f'Method not allowed: {request.method} {request.path}')
    return jsonify({
        'error': 'Method not allowed',
        'path': request.path,
        'method': request.method,
        'allowed_methods': error.valid_methods
    }), 405


@main_bp.errorhandler(500)
def internal_error(error) -> Response:
    """
    Handle 500 internal server errors.
    
    Args:
        error: The error that occurred
    
    Returns:
        JSON response with error details
    """
    logger.error(f'Internal server error: {str(error)}')
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500