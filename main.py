#Importación de módulos y bibliotecas.
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Text, Optional
from datetime import datetime
from uuid import uuid4 as uuid

import aiohttp
import time
import asyncio
import uvicorn

#Inicio de la aplicación.
app = FastAPI()
#URL de la PokeAPI
url = 'https://pokeapi.co/api/v2/pokemon/'
#Inicialización de la colección de Pokémon.
pokemones = []

#Definición de ruta para archivos estáticos.
app.mount("/static", StaticFiles(directory="static"), name="static")
#Definición de ruta para templates html.
templates = Jinja2Templates(directory="templates")

#Se inicia la sesión desde el inicio de la aplicación.
@app.on_event('startup')
async def startup_event():
    #Creación de sesión.
    global session 
    session = aiohttp.ClientSession()
    print("Iniciando sesion")

#Se cierra la sesión al apagarse la aplicación.
@app.on_event('shutdown')
async def shutdown_event():
    await session.close()
    print("Cerrando sesion")

#Middleware que agrega el tiempo de procesamiento de la solicitud.
@app.middleware("http")
async def process_time(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    print(process_time)
    return response

#Clase Pokémon.
class Pokemon(BaseModel):
    id: Optional[str]
    pokeID: int
    name: str
    type: str
    height: float
    weight: float
    image: str
    captured_at: datetime = datetime.now()

#Se muestra el index de la aplicación.
@app.get("/")
async def index(request: Request, response_class=HTMLResponse):
    return templates.TemplateResponse("index.html", {"request": request})

#Captura un nuevo Pokémon para la colección.
@app.post('/capturar/{poke_nid}')
async def catch_pokemon(poke_nid: str, request: Request):
    #Se busca al Pokémon en la PokéAPI y se obtienen sus datos.
    async with session.get(f"{url}{poke_nid}") as resp:
        pokedata = await resp.json()

        #Se extraen los datos del JSON devuelto.
        id = str(uuid())
        pokeID = pokedata["id"]
        name = pokedata["name"]
        weight = round(pokedata["weight"]*0.1, 2)
        height = round(pokedata["height"]*0.1, 2)
        image = pokedata['sprites']['other']['official-artwork']['front_default']
    
        #Se obtiene el tipo en español.
        url_aux = pokedata['types'][0]['type']['url']
        async with session.get(url_aux) as resp:
            poketype = await resp.json()
            type = poketype['names'][5]['name']
    
            #Se guarda el Pokémon en un objeto.
            pokemon = Pokemon(id=id, pokeID=pokeID, name=name, weight=weight, height=height, image=image, type=type)
            #Se guarda el Pokémon en la colección de archivos JSON.
            pokemones.append(pokemon.dict())
            #Se muestra el ejemplar recién capturado.
            return templates.TemplateResponse("showPokemon.html", {
                "request": request,
                "pokemon": pokemon
                })

#Muestra a los Pokémon capturados.
@app.get('/pokemones')
async def get_pokemones(request: Request):
    return templates.TemplateResponse("showAllPokemon.html", {
        "request": request,
        "pokemones": pokemones
        })

#Muestra a un Pokémon en específico de los ya capturados.
@app.get('/pokemon/pokemon_id+={pokemon_id}')
async def get_pokemon(pokemon_id: str, request: Request):
    #Se busca al Pokémon en la colección.
    for pokemon in pokemones:
        #Se encuentra el Pokémon y se muestra.
        if pokemon["id"] == pokemon_id:
            return templates.TemplateResponse("showPokemon.html", {
            "request": request,
            "pokemon": pokemon
            })
    #El Pokémon no fue encontrado.
    return templates.TemplateResponse("message.html", {
        "request": request, 
        "message": "Pokémon NO encontrado."}, 
        status_code=404)

#Muestra a un pokemón en específico de los ya capturados (función con URL más simple).
@app.get('/pokemon/{pokemon_id}')
async def get_pokemon(pokemon_id: str, request: Request):
    #Se busca al Pokémon en la colección.
    for pokemon in pokemones:
        #Se encuentra el Pokémon y se muestra.
        if pokemon["id"] == pokemon_id:
            return templates.TemplateResponse("showPokemon.html", {
            "request": request,
            "pokemon": pokemon
            })
    #El Pokémon no fue encontrado.
    return templates.TemplateResponse("message.html", {
        "request": request, 
        "message": "Pokémon NO encontrado."}, 
        status_code=404)

#Libera (elimina) a un Pokémon.
@app.get("/eliminar/del_pokemon_id+={del_pokemon_id}")
async def release_pokemon(del_pokemon_id: str, request: Request):
    #Se busca al Pokémon en la colección.
    for index, pokemon in enumerate(pokemones):
        #Se encuentra el Pokémon y se elimina de la colección.
        if pokemon["id"] == del_pokemon_id:
                pokemones.pop(index)
                return templates.TemplateResponse("message.html", {
                    "request": request, 
                    "message": "El Pokémon ha sido liberado con éxito"
                })
    #El Pokémon no fue encontrado.
    return templates.TemplateResponse("message.html", {
        "request": request, 
        "message": "Pokémon NO encontrado."}, 
        status_code=404)

#Función que trata el error 404.
@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse("message.html", {
        "request": request, 
        "message": "Algo salió mal =("}, 
        status_code=404)
