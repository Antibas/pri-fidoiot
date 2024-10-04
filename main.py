from fastapi import FastAPI, APIRouter, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import subprocess, os, aiomysql

app = FastAPI()

origins = [
    "http://localhost:5173",  # Vue.js dev server
    "http://127.0.0.1:5173",  # Alternate localhost form
    # You can add more origins here as needed (e.g., production URLs)
]

# Add CORS middleware to your FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows specific origins
    allow_credentials=True,  # Allows cookies and credentials
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

router = APIRouter(prefix="/dashboard")

PATH = 'component-samples/demo/scripts/'
DEMOPATH = 'component-samples/demo/'
COMPONENTS = ["db", 'aio', 'rv', 'owner', 'manufacturer', 'device', 'reseller']

outlog = lambda out: (out.stderr if out.stderr else out.stdout) + "\n"

@router.get("/generate_certificates")
async def generate_certificates():
    try:
        log = ""
        #Generating demo certificate authority KeyPair and certificate
        out = subprocess.run(f"./demo_ca.sh", cwd=PATH, shell=True, capture_output=True, text=True)
        print(out.returncode)
        if out.returncode:
            raise Exception(out.stderr)
        log += outlog(out)

        #Generating Server and Client Keypair and certificates.
        out = subprocess.run(f"bash web_csr_req.sh", cwd=PATH, shell=True, capture_output=True, text=True)
        print(out.returncode)
        if out.returncode:
            raise Exception(out.stderr)
        log += outlog(out)

        out = subprocess.run(f"bash user_csr_req.sh", cwd=PATH,shell=True, capture_output=True, text=True)
        print(out.returncode)
        if out.returncode:
            raise Exception(out.stderr)
        log += outlog(out)

        #Generate random passwords & secrets
        out = subprocess.run(f"./keys_gen.sh",  cwd=PATH, shell=True, capture_output=True, text=True)
        print(out.returncode)
        if out.returncode:
            raise Exception(out.stderr)
        log += outlog(out)

        #Copy secrets
        for component in COMPONENTS:
            out = subprocess.run(f"cp -r ./secrets/. ../{component}/secrets/", cwd=PATH, shell=True, capture_output=True, text=True)
            print(out.returncode)
            if out.returncode:
                raise Exception(out.stderr)
            # if component != "db":
            #     out = subprocess.run(f"cp service.env ../{component}/", cwd=PATH, shell=True, capture_output=True, text=True)
            #     print(out.returncode)
            #     if out.returncode:
            #         raise Exception(out.stderr)
        return Response(content=log)
    except Exception as e:
        return Response(content=e.__str__(), status_code=500)

@router.get("/start/{component_name}")
async def start_component(component_name: str):
    if not component_name in COMPONENTS:
        return Response(content=f"Component {component_name} not found.", status_code=404)
    try:
        out = subprocess.run(f"sudo docker-compose up --build -d", cwd=f'{DEMOPATH}{component_name}', shell=True, capture_output=True, text=True)
        print(out.returncode)
        if out.returncode:
            raise Exception(out.stderr)
        return Response(content=outlog(out))
    except Exception as e:
        return Response(content=e.__str__(), status_code=500)
    
@router.get("/stop/{component_name}")
async def stop_component(component_name: str):
    if not component_name in COMPONENTS:
        return Response(content=f"Component {component_name} not found.", status_code=404)
    try:
        out = subprocess.run(f"cd {DEMOPATH}{component_name}; sudo docker-compose down", shell=True, capture_output=True, text=True)
        return Response(content=outlog(out))
    except Exception as e:
        return Response(content=e.__str__(), status_code=500)

@router.get("/db/{database_name}/{table_name}")
async def get_database(database_name: str, table_name: str):
    conn = await aiomysql.connect(
        host="localhost",
        port=3306,
        user="root",
        password="QUS8R1GXTeTRlc5",
        db=database_name
    )
    cursor = await conn.cursor()
    await cursor.execute(f"SELECT * FROM {table_name}")
    result = await cursor.fetchall()
    conn.close()
    return result

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)