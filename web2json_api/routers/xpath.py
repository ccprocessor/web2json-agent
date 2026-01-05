"""
XPath生成 API

简化版：只有一个核心endpoint
"""
from fastapi import APIRouter, HTTPException
from loguru import logger

from web2json_api.models.xpath import XPathGenerateRequest, XPathGenerateResponse
from web2json_api.services.xpath_service import xpath_service

router = APIRouter()


@router.post("/generate", response_model=XPathGenerateResponse)
async def generate_xpaths(request: XPathGenerateRequest):
    """
    生成XPath表达式（支持多样本迭代）

    **核心功能：**
    1. 接收多个HTML内容或URL（推荐2-5个样本）
    2. 接收字段定义
    3. 对每个样本调用agent生成XPath
    4. 合并结果，返回最优XPath

    **请求示例1（多个HTML内容）：**
    ```json
    {
      "html_contents": [
        "<html><body><h1>Title 1</h1><span class='price'>$99.99</span></body></html>",
        "<html><body><h1>Title 2</h1><span class='price'>$89.99</span></body></html>"
      ],
      "fields": [
        {"name": "title", "description": "Page title", "field_type": "string"},
        {"name": "price", "description": "Product price", "field_type": "string"}
      ],
      "iteration_rounds": 2
    }
    ```

    **请求示例2（多个URL）：**
    ```json
    {
      "urls": [
        "https://example.com/product/1",
        "https://example.com/product/2",
        "https://example.com/product/3"
      ],
      "fields": [
        {"name": "title", "description": "Product title"},
        {"name": "price", "description": "Product price"}
      ]
    }
    ```

    **请求示例3（单个，兼容旧版）：**
    ```json
    {
      "html_content": "<html>...</html>",
      "fields": [...]
    }
    ```

    **响应示例：**
    ```json
    {
      "success": true,
      "fields": [
        {
          "name": "title",
          "xpath": "//h1/text()",
          "value_sample": ["Title 1", "Title 2"]
        }
      ],
      "message": "Successfully generated XPath for 2 field(s) using 2 samples"
    }
    ```
    """
    try:
        # 验证输入：至少提供一种输入方式
        has_input = bool(
            request.html_contents or
            request.urls or
            request.html_content or
            request.url
        )

        if not has_input:
            raise HTTPException(
                status_code=400,
                detail="Must provide at least one of: html_contents, urls, html_content, or url"
            )

        if not request.fields or len(request.fields) == 0:
            raise HTTPException(status_code=400, detail="At least one field is required")

        # 统计样本数
        sample_count = 0
        if request.html_contents:
            sample_count += len(request.html_contents)
        if request.urls:
            sample_count += len(request.urls)
        if request.html_content:
            sample_count += 1
        if request.url:
            sample_count += 1

        logger.info(f"收到XPath生成请求: {len(request.fields)} 个字段, {sample_count} 个样本")

        # 调用服务生成XPath
        output_fields = xpath_service.generate_xpaths(
            html_contents=request.html_contents,
            html_content=request.html_content,
            fields=request.fields,
            iteration_rounds=request.iteration_rounds
        )

        iteration_rounds = request.iteration_rounds or sample_count
        return XPathGenerateResponse(
            success=True,
            fields=output_fields,
            message=f"Successfully generated XPath for {len(output_fields)} field(s) using {iteration_rounds} sample(s)"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"XPath生成失败: {str(e)}")
        return XPathGenerateResponse(
            success=False,
            fields=[],
            error=str(e),
            message="Failed to generate XPath"
        )
