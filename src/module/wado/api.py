import requests

from typing import Union

from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response

from config.settings import settings

from httpx import AsyncClient

async def get_client():
    # create a new client for each request
    async with AsyncClient() as client:
        # yield the client to the endpoint function
        yield client
        # close the client when the request is done

router = APIRouter(prefix="/ws/rest/wado-rs", tags=['wado-rs'])

@router.get("/{sessionID}/studies/{studyUID}/series")
async def get_study(sessionID: str, studyUID: str) -> Response:
    async with AsyncClient() as client:
        resp = await client.get(f"{settings.WADO_URL}/studies/{studyUID}/series", auth= (settings.WADO_USER, settings.WADO_PASSWORD))
    
    return JSONResponse(resp.json())
    # return JSONResponse(requests.get(f"{settings.WADO_URL}/studies/{studyUID}/series",
                # auth = (settings.WADO_USER, settings.WADO_PASSWORD)).json())

@router.get("/{sessionID}/studies/{studyUID}/series/{seriesUID}/metadata")
async def get_series_metadata(sessionID: str, studyUID: str, seriesUID: str) -> Response:
    async with AsyncClient() as client:
        resp = await client.get(f"{settings.WADO_URL}/studies/{studyUID}/series/{seriesUID}/metadata", auth= (settings.WADO_USER, settings.WADO_PASSWORD))
    return Response(content = resp.read(), media_type="application/octet-stream")
    # return Response(content=requests.get(f"{settings.WADO_URL}/studies/{studyUID}/series/{seriesUID}/metadata",
                # auth = (settings.WADO_USER, settings.WADO_PASSWORD)).content, media_type="application/octet-stream")

@router.get("/{sessionID}/studies/{studyUID}/series/{seriesUID}/instances/{sopUID}/frames/{frames}")
async def get_frame(sessionID: str, studyUID: str, seriesUID: str, sopUID: str, frames: str) -> Response:
    async with AsyncClient() as client:
        resp = await client.get(f"{settings.WADO_URL}/studies/{studyUID}/series/{seriesUID}/instances/{sopUID}/frames/{frames}", auth= (settings.WADO_USER, settings.WADO_PASSWORD))
    
    return Response(content = resp.read(), media_type="application/octet-stream")


    # return Response(requests.get(f"{settings.WADO_URL}/studies/{studyUID}/series/{seriesUID}/instances/{sopUID}/frames/{frames}",
    #              auth = (settings.WADO_USER, settings.WADO_PASSWORD)).content, media_type="application/octet-stream")

@router.get("/{sessionID}/studies/{studyUID}/series/{seriesUID}/thumbnail")
async def get_series_thumbnail(sessionID: str, studyUID: str, seriesUID: str, q: Union[str, None] = None, viewport: str = "") -> Response:
    async with AsyncClient() as client:
        resp = await client.get(f"{settings.WADO_URL}/studies/{studyUID}/series/{seriesUID}/thumbnail", auth= (settings.WADO_USER, settings.WADO_PASSWORD))
    
    return Response(content = resp.read(), media_type="application/octet-stream")

    # return Response(content=requests.get(f"{settings.WADO_URL}/studies/{studyUID}/series/{seriesUID}/thumbnail",
    #             params=viewport,
    #             auth = (settings.WADO_USER, settings.WADO_PASSWORD)).content,
                # content_type = "image/jpeg")

@router.get("/{sessionID}/studies/{studyUID}/series/{seriesUID}/instances/{sopUID}/frames/{frames}/thumbnail")
async def get_series_thumbnail(sessionID: str, studyUID: str, seriesUID: str, sopUID: str, frames: str, q: Union[str, None] = None, viewport: str = "") -> Response:
    async with AsyncClient() as client:
        resp = await client.get(f"{settings.WADO_URL}/studies/{studyUID}/series/{seriesUID}/instances/{sopUID}/frames/{frames}/thumbnail", auth= (settings.WADO_USER, settings.WADO_PASSWORD))
    
    return Response(content = resp.read(), media_type="application/octet-stream")

    # return Response(content=requests.get(f"{settings.WADO_URL}/studies/{studyUID}/series/{seriesUID}/instances/{sopUID}/frames/{frames}/thumbnail",
    #             params=viewport,
    #             auth = (settings.WADO_USER, settings.WADO_PASSWORD)).content,
    #             media_type = "image/jpeg")

