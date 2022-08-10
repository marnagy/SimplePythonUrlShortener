from threading import Thread
from flask import Flask, request, render_template, redirect, Response, jsonify, url_for
from os import environ
import asyncio
from time import sleep
from random import Random
from db import (UrlRecordModel, decode, get_code_for,
                Session, close_connection, AsyncSession)
from typing import Callable, Optional

def get_async_delete(url_model: UrlRecordModel, session: AsyncSession, hours: int) -> Callable[[], None]:
    def res_func():
        sleep(hours * 60 * 60)
        session.delete(url_model)
        asyncio.run(session.commit())
        UrlRecordModel.USED_NUMBERS.remove(url_model.id)
        print(f'Model {url_model.id} was deleted.')

    return res_func

app = Flask('Url shortener')

PORT = None
DEBUG = False
try:
    PORT = environ.get('PORT')
except:
    PORT = 5_000
    DEBUG = True

@app.get('/test')
def test():
    return jsonify({
        'Hello': 'world!'
    })

@app.get('/async-test')
async def async_test():
    await asyncio.sleep(2)
    return jsonify({
        'Hello': 'world!'
    })

### API ###
@app.get('/api/shorten')
async def api_shorten():
    url = request.args.get('url')

    code, url_model = UrlRecordModel.CreateNew(url)

    if code is None or url_model is None:
        return Response('Invalid string: not valid url.', 400)
    
    Session.add(url_model)
    await Session.commit()
    #print(f'Created number {number} for code {shortened}')
    thread = Thread(target=get_async_delete(url_model, Session, 10))
    thread.start()
    returned_url = f'{request.host_url}{code}'
    return {
        'url': returned_url
    }

@app.get('/<string:code>')
async def redirect_to_url(code:str):
    if code == 'favicon.ico':
        return Response(status=500)

    valid, number = decode(code)
    #print(f'Decoded code {code} as number {number}')

    if valid and number in UrlRecordModel.USED_NUMBERS:
        url_model: Optional[UrlRecordModel] = await Session.get(UrlRecordModel, number)
        if url_model is None:
            return Response(f'Failed to load URL.', 500)

        response_url = url_model.url
        #print(f'Redirecting to {response_url}')
        return Response(status=301, headers={
            'Location': response_url
        })
    else:
        return Response(f'Invalid code provided.', 400)

async def async_main():
    try:
        app.run(host='0.0.0.0', port=PORT, debug=DEBUG, threaded=True)
    finally:
        await close_connection()

if __name__ == '__main__':
    asyncio.run(async_main())
