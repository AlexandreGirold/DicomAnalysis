from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/analysis")
async def analysis_endpoint():
    return {"message": "This is the analysis endpoint"}