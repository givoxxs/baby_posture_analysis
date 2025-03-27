"""
Analysis router for historical data and trends.

This module provides endpoints for retrieving historical pose analysis data
and generating trend reports.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
import logging
from datetime import datetime, timedelta

from app.repositories.factory import get_analysis_repository
from app.models.analysis import PoseAnalysisRecord
from app.utils.error_handling import handle_exceptions, NotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/analysis",
    tags=["analysis"]
)


@router.get("/history", response_model=List[PoseAnalysisRecord])
@handle_exceptions
async def get_analysis_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    repository=Depends(get_analysis_repository)
):
    """
    Get historical pose analysis results.
    
    Parameters:
    - limit: Maximum number of results to return
    - offset: Number of results to skip
    
    Returns:
    - List of historical pose analysis records
    """
    logger.info(f"Retrieving analysis history (limit={limit}, offset={offset})")
    records = await repository.list(limit=limit, offset=offset)
    return records


@router.get("/trends")
@handle_exceptions
async def get_analysis_trends(
    days: int = Query(7, ge=1, le=30),
    repository=Depends(get_analysis_repository)
):
    """
    Get trend analysis of pose data over time.
    
    Parameters:
    - days: Number of days to include in trend analysis
    
    Returns:
    - Trend analysis data
    """
    logger.info(f"Calculating trends for the past {days} days")
    
    # Get all records
    all_records = await repository.list(limit=1000)
    
    # Filter to records within the date range
    cutoff_date = datetime.now() - timedelta(days=days)
    recent_records = [
        record for record in all_records 
        if isinstance(record.get('timestamp'), str) and 
        datetime.fromisoformat(record.get('timestamp')) >= cutoff_date
    ]
    
    # Group by risk level and pose type
    risk_levels = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    pose_types = {}
    
    for record in recent_records:
        # Count risk levels
        risk_level = record.get('risk_level', 'unknown')
        if risk_level in risk_levels:
            risk_levels[risk_level] += 1
        
        # Count pose types
        pose_type = record.get('pose_type', 'unknown')
        if pose_type in pose_types:
            pose_types[pose_type] += 1
        else:
            pose_types[pose_type] = 1
    
    return {
        "days_analyzed": days,
        "total_records": len(recent_records),
        "risk_level_distribution": risk_levels,
        "pose_type_distribution": pose_types
    }


@router.get("/record/{record_id}", response_model=PoseAnalysisRecord)
@handle_exceptions
async def get_analysis_record(
    record_id: str,
    repository=Depends(get_analysis_repository)
):
    """
    Get a specific analysis record by ID.
    
    Parameters:
    - record_id: ID of the record to retrieve
    
    Returns:
    - The requested pose analysis record
    """
    logger.info(f"Retrieving analysis record {record_id}")
    record = await repository.get_by_id(record_id)
    if not record:
        raise NotFoundError(f"Analysis record with ID {record_id} not found")
    return record
