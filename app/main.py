from fastapi import FastAPI

app = FastAPI(title="AurFX Backend")


@app.get("/")
def root():
    return {"message": "AurFX Backend is running"}