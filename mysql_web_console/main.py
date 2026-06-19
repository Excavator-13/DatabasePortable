from fastapi import FastAPI

app = FastAPI(title="MySQL Web Console")


@app.get("/")
async def root():
    return {"message": "Server is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)