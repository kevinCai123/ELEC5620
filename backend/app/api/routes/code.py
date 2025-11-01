from __future__ import annotations

from fastapi import APIRouter, Depends

from app.schemas.code import (
    CodeExecutionRequest,
    CodeExecutionResponse,
    CodeGenerationRequest,
    CodeGenerationResponse,
)
from app.services.code import CodeService

router = APIRouter()


def get_code_service() -> CodeService:
    return CodeService()


@router.post("/code/generate", response_model=CodeGenerationResponse, tags=["code"])
async def generate_code(
    payload: CodeGenerationRequest,
    service: CodeService = Depends(get_code_service),
) -> CodeGenerationResponse:
    """Generate code from natural language prompt using AI"""
    code, explanation, fallback_used = await service.generate_code(payload.prompt, payload.language)
    return CodeGenerationResponse(
        code=code,
        language=payload.language,
        explanation=explanation,
        fallback_used=fallback_used,
    )


@router.post("/code/execute", response_model=CodeExecutionResponse, tags=["code"])
async def execute_code(
    payload: CodeExecutionRequest,
    service: CodeService = Depends(get_code_service),
) -> CodeExecutionResponse:
    """Execute code with LLM-powered analysis (safety check before, insights after)"""
    (
        pre_analysis,
        output,
        error,
        execution_time,
        success,
        post_analysis,
        fallback_used,
    ) = await service.execute_code_with_llm_analysis(
        payload.code, payload.language, payload.timeout
    )
    return CodeExecutionResponse(
        pre_analysis=pre_analysis,
        output=output,
        error=error,
        execution_time=execution_time,
        success=success,
        post_analysis=post_analysis,
        fallback_used=fallback_used,
    )


__all__ = ["router"]

