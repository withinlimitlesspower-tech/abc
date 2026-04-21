"""
Models module for Project application.
Contains all data models and related functionality.
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

import pydantic
from pydantic import BaseModel, Field, validator

# Configure logging
logger = logging.getLogger(__name__)


class Status(Enum):
    """Enumeration for entity status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    DELETED = "deleted"


class BaseEntity(ABC):
    """Abstract base class for all entities."""
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary representation."""
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate entity data."""
        pass
    
    def to_json(self) -> str:
        """Convert entity to JSON string."""
        try:
            return json.dumps(self.to_dict(), default=str)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize entity to JSON: {e}")
            raise ValueError(f"Serialization error: {e}")


@dataclass
class User(BaseEntity):
    """User model representing application users."""
    
    id: UUID = field(default_factory=uuid4)
    username: str
    email: str
    full_name: Optional[str] = None
    status: Status = Status.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization validation."""
        if not self.username.strip():
            raise ValueError("Username cannot be empty")
        if "@" not in self.email:
            raise ValueError("Invalid email format")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary."""
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }
    
    def validate(self) -> bool:
        """Validate user data."""
        try:
            if not self.username or len(self.username) < 3:
                return False
            if "@" not in self.email or "." not in self.email.split("@")[-1]:
                return False
            return True
        except Exception as e:
            logger.error(f"User validation failed: {e}")
            return False
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()


class Project(BaseModel):
    """Project model using Pydantic for validation."""
    
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    owner_id: UUID
    status: Status = Status.PENDING
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            UUID: str,
            datetime: lambda dt: dt.isoformat(),
            Status: lambda s: s.value
        }
        validate_assignment = True
    
    @validator('name')
    def validate_name(cls, v):
        """Validate project name."""
        if not v.strip():
            raise ValueError("Project name cannot be empty")
        return v.strip()
    
    @validator('end_date')
    def validate_dates(cls, v, values):
        """Validate that end_date is after start_date if both exist."""
        if v and 'start_date' in values and values['start_date']:
            if v <= values['start_date']:
                raise ValueError("End date must be after start date")
        return v
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()
    
    def add_tag(self, tag: str):
        """Add a tag to the project."""
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.update_timestamp()
    
    def remove_tag(self, tag: str):
        """Remove a tag from the project."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.update_timestamp()


class Task(BaseModel):
    """Task model representing project tasks."""
    
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    assignee_id: Optional[UUID] = None
    priority: int = Field(default=1, ge=1, le=5)
    status: Status = Status.PENDING
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    actual_hours: float = Field(default=0.0, ge=0)
    dependencies: List[UUID] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            UUID: str,
            datetime: lambda dt: dt.isoformat(),
            Status: lambda s: s.value
        }
    
    @validator('title')
    def validate_title(cls, v):
        """Validate task title."""
        if not v.strip():
            raise ValueError("Task title cannot be empty")
        return v.strip()
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()
    
    def add_dependency(self, task_id: UUID):
        """Add a task dependency."""
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)
            self.update_timestamp()
    
    def remove_dependency(self, task_id: UUID):
        """Remove a task dependency."""
        if task_id in self.dependencies:
            self.dependencies.remove(task_id)
            self.update_timestamp()
    
    def log_hours(self, hours: float):
        """Log actual hours worked on the task."""
        if hours < 0:
            raise ValueError("Hours cannot be negative")
        self.actual_hours += hours
        self.update_timestamp()


class ModelFactory:
    """Factory class for creating model instances."""
    
    @staticmethod
    def create_user(
        username: str,
        email: str,
        full_name: Optional[str] = None,
        **kwargs
    ) -> User:
        """Create a new User instance."""
        try:
            return User(
                username=username,
                email=email,
                full_name=full_name,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise ValueError(f"User creation failed: {e}")
    
    @staticmethod
    def create_project(
        name: str,
        owner_id: UUID,
        description: Optional[str] = None,
        **kwargs
    ) -> Project:
        """Create a new Project instance."""
        try:
            return Project(
                name=name,
                owner_id=owner_id,
                description=description,
                **kwargs
            )
        except pydantic.ValidationError as e:
            logger.error(f"Project validation failed: {e}")
            raise ValueError(f"Invalid project data: {e}")
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            raise ValueError(f"Project creation failed: {e}")
    
    @staticmethod
    def create_task(
        project_id: UUID,
        title: str,
        assignee_id: Optional[UUID] = None,
        **kwargs
    ) -> Task:
        """Create a new Task instance."""
        try:
            return Task(
                project_id=project_id,
                title=title,
                assignee_id=assignee_id,
                **kwargs
            )
        except pydantic.ValidationError as e:
            logger.error(f"Task validation failed: {e}")
            raise ValueError(f"Invalid task data: {e}")
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            raise ValueError(f"Task creation failed: {e}")


class ModelSerializer:
    """Serializer for model objects."""
    
    @staticmethod
    def serialize(obj: Union[User, Project, Task]) -> Dict[str, Any]:
        """Serialize a model object to dictionary."""
        try:
            if isinstance(obj, User):
                return obj.to_dict()
            elif isinstance(obj, (Project, Task)):
                return obj.dict()
            else:
                raise TypeError(f"Unsupported object type: {type(obj)}")
        except Exception as e:
            logger.error(f"Serialization failed: {e}")
            raise ValueError(f"Failed to serialize object: {e}")
    
    @staticmethod
    def deserialize_user(data: Dict[str, Any]) -> User:
        """Deserialize dictionary to User object."""
        try:
            # Convert string UUID to UUID object if needed
            if isinstance(data.get('id'), str):
                data['id'] = UUID(data['id'])
            
            # Convert string status to Status enum if needed
            if isinstance(data.get('status'), str):
                data['status'] = Status(data['status'])
            
            # Convert string timestamps to datetime objects if needed
            for time_field in ['created_at', 'updated_at']:
                if isinstance(data.get(time_field), str):
                    data[time_field] = datetime.fromisoformat(data[time_field])
            
            return User(**data)
        except Exception as e:
            logger.error(f"User deserialization failed: {e}")
            raise ValueError(f"Failed to deserialize user: {e}")


class ModelValidator:
    """Validator for model objects."""
    
    @staticmethod
    def validate_user(user: User) -> List[str]:
        """Validate user and return list of errors."""
        errors = []
        
        try:
            if not user.username or len(user.username) < 3:
                errors.append("Username must be at least 3 characters")
            
            if not user.email or "@" not in user.email:
                errors.append("Invalid email format")
            
            if user.status not in Status:
                errors.append(f"Invalid status: {user.status}")
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return errors
    
    @staticmethod
    def validate_project(project: Project) -> List[str]:
        """Validate project and return list of errors."""
        errors = []
        
        try:
            if not project.name or len(project.name.strip()) == 0:
                errors.append("Project name is required")
            
            if project.end_date and project.start_date:
                if project.end_date <= project.start_date:
                    errors.append("End date must be after start date")
            
            if project.tags:
                for tag in project.tags:
                    if not isinstance(tag, str) or len(tag.strip()) == 0:
                        errors.append("Invalid tag found")
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return errors
    
    @staticmethod
    def validate_task(task: Task) -> List[str]:
        """Validate task and return list of errors."""
        errors = []
        
        try:
            if not task.title or len(task.title.strip()) == 0:
                errors.append("Task title is required")
            
            if task.priority < 1 or task.priority > 5:
                errors.append("Priority must be between 1 and 5")
            
            if task.estimated_hours is not None and task.estimated_hours < 0:
                errors.append("Estimated hours cannot be negative")
            
            if task.actual_hours < 0:
                errors.append("Actual hours cannot be negative")
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return errors


# Export public classes and functions
__all__ = [
    'Status',
    'User',
    'Project',
    'Task',
    'ModelFactory',
    'ModelSerializer',
    'ModelValidator',
    'BaseEntity'
]