from fastapi import APIRouter, UploadFile, File, Form, Query, HTTPException
import shutil
import os
import json
from datetime import datetime
import glob

router = APIRouter()

@router.post("/upload/")
async def upload_video(
    user_id: str = Form(...),
    file: UploadFile = File(...),
    lift_type: str = Form(...),
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

    metadata_files = glob.glob(f"{video_dir}/*.json") # find all .json files in videos/
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
    filename: str = Form(...)
):
    user_dir = os.path.join("videos", user_id)
    video_path = os.path.join(user_dir, filename)

    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not found")
    
    # for now, return fake feedback
    feedback = {
        "lift_type": "squat",
        "depth": "below parallel",
        "back_position": "neutral",
        "knee_tracking": "knees caving in slightly",
        "verdict": "Needs improvement"
    }

    return {"filename": filename, "feedback": feedback}