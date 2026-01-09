"""
Configuration API router
Handles API key and settings management
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from dotenv import load_dotenv, set_key
import os
from typing import Optional

router = APIRouter()


class ConfigGetResponse(BaseModel):
    """Get configuration response"""
    api_key: str
    api_base: str
    iteration_rounds: int
    masked_api_key: str


class ConfigUpdateRequest(BaseModel):
    """Update configuration request"""
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    iteration_rounds: Optional[int] = None


class ConfigUpdateResponse(BaseModel):
    """Update configuration response"""
    success: bool
    message: str


def mask_api_key(api_key: str) -> str:
    """
    Mask API key by hiding middle characters
    Shows first 7 and last 4 characters
    """
    if not api_key or len(api_key) < 12:
        return "****"

    return f"{api_key[:7]}...{api_key[-4:]}"


def get_env_file_path() -> Path:
    """Get .env file path"""
    # Check current working directory first
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        return cwd_env

    # Fallback to package directory
    package_env = Path(__file__).parent.parent.parent / ".env"
    if package_env.exists():
        return package_env

    # Return cwd path if neither exists (will be created)
    return cwd_env


@router.get("/config", response_model=ConfigGetResponse)
async def get_config():
    """
    Get current configuration
    Returns masked API key for display
    """
    try:
        # Reload environment variables
        env_path = get_env_file_path()
        if env_path.exists():
            load_dotenv(env_path, override=True)

        api_key = os.getenv("OPENAI_API_KEY", "")
        api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        iteration_rounds = int(os.getenv("DEFAULT_ITERATION_ROUNDS", "3"))

        return ConfigGetResponse(
            api_key=api_key,
            api_base=api_base,
            iteration_rounds=iteration_rounds,
            masked_api_key=mask_api_key(api_key)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")


@router.post("/config", response_model=ConfigUpdateResponse)
async def update_config(request: ConfigUpdateRequest):
    """
    Update configuration
    Updates .env file with new values
    """
    try:
        env_path = get_env_file_path()

        # Create .env if it doesn't exist
        if not env_path.exists():
            env_path.touch()

        updated_fields = []

        # Update API key
        if request.api_key is not None:
            set_key(str(env_path), "OPENAI_API_KEY", request.api_key, quote_mode='never')
            updated_fields.append("API Key")

        # Update API base
        if request.api_base is not None:
            set_key(str(env_path), "OPENAI_API_BASE", request.api_base, quote_mode='never')
            updated_fields.append("API Base URL")

        # Update iteration rounds
        if request.iteration_rounds is not None:
            set_key(str(env_path), "DEFAULT_ITERATION_ROUNDS", str(request.iteration_rounds), quote_mode='never')
            updated_fields.append("Iteration Rounds")

        # Reload environment variables
        load_dotenv(env_path, override=True)

        # Also update the settings instance
        from web2json.config.settings import settings
        if request.api_key is not None:
            settings.openai_api_key = request.api_key
        if request.api_base is not None:
            settings.openai_api_base = request.api_base
        if request.iteration_rounds is not None:
            settings.default_iteration_rounds = request.iteration_rounds

        message = f"Successfully updated: {', '.join(updated_fields)}"

        return ConfigUpdateResponse(
            success=True,
            message=message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")
