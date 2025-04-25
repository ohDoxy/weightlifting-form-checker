from fastapi import APIRouter, UploadFile, File, Form, Query, HTTPException
import shutil
import os
import json
from datetime import datetime
import glob
from .analyzer import analyze_video

router = APIRouter()

@router.post("/upload/")
async def upload_video(
    user_id: str = Form(...),
    file: UploadFile = File(...),
    lift_type: str = Form(...),
    side: str = Form("right"),
    notes: str = Form(None)
):
    # create the user directory (if it doesn't exist already)
    user_dir = os.path.join("videos", user_id)
    os.makedirs(user_dir, exist_ok=True)

    # make sure the videos/ directory exists
    video_dir = "videos"
    os.makedirs(video_dir, exist_ok=True)

    file_path = os.path.join(user_dir, file.filename) # /videos/user/file
    # saves the uploaded file to disk in chunks without loading the whole thing in memory
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # build metadata
    metadata = {
        "user_id": user_id,
        "filename": file.filename,
        "upload_time": datetime.now().isoformat(),
        "lift_type": lift_type,
        "side": side,
        "notes": notes
    }

    # save metadata json
    metadata_path = os.path.splitext(file_path)[0] + ".json"
    with open(metadata_path, "w") as meta_file:
        json.dump(metadata, meta_file, indent=4)
    
    return {"filename": file.filename, "metadata": metadata}


@router.get("/history/")
def get_history(user_id: str = Query(...)):
    video_dir = os.path.join("videos", user_id)

    # check if user_id exists
    if not os.path.exists(video_dir):
        raise HTTPException(status_code=404, detail="User not found")

    metadata_files = glob.glob(f"{video_dir}/*.json") # find all .json files in videos/user_id
    history = []

    # read each metadata file and add it to the history list
    for meta_path in metadata_files:
        with open(meta_path, "r") as f:
            data = json.load(f)
            history.append(data)
    
    return {"history": history}


@router.post("/feedback/")
def get_feedback(
    user_id: str = Form(...),
    filename: str = Form(...),
):
    user_dir = os.path.join("videos", user_id)
    if not filename.endswith(".mov"):
        filename += ".mov"

    video_path = os.path.join(user_dir, filename)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail=f"Video not found, path={video_path}")
    
    metadata_path = os.path.splitext(video_path)[0] + ".json" # get json data for this video
    if not os.path.exists(metadata_path):
        raise HTTPException(status_code=404, detail=f"Metadata not found, path={metadata_path}")
    
    # get the side of analysis stored in the json data
    with open(metadata_path, "r") as meta_file:
        metadata = json.load(meta_file)
        side = metadata.get("side", "right") # default to right if missing
    
    # real feedback from analyzer
    feedback = analyze_video(video_path, side)

    return {"filename": filename, "feedback": feedback}