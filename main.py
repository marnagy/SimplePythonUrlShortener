from threading import Thread
from flask import Flask, request, render_template, redirect, Response, jsonify, url_for
from os import environ
import string
import asyncio
from time import sleep
from random import Random
from validators import url as url_validate


BASE_64 = string.ascii_letters + string.digits + '-' + '%'
base = len(BASE_64)
rng = Random()
url_addresses: dict[int, str]  = dict()

def convert_to_BASE64(num: int) -> tuple[bool, str]:
    if not isinstance(num, int):
        return (False, None)
    
    res_idx: list[int] = list()
    while num > 0:
        res_idx.append(num % base)
        num = num // base
    
    return (True, ''.join(
            map(
                lambda i: BASE_64[i],
                res_idx[::-1]
            )
        )
    )

def convert_from_BASE64(code: str) -> tuple[bool, int]:
    if any(map(lambda x: x not in BASE_64, code)):
        return (False, -1)
    
    indices = list(map(
        lambda c: BASE_64.index(c),
        code
    ))
    current_power = 0
    base = len(BASE_64)
    number = 0
    for i in indices[::-1]:
        number += i * pow(base, current_power)
        current_power += 1
    
    return (True, number)

def delete_after(number: int, hours: int) -> None:
    sleep(hours * 60 * 60)
    url_addresses.pop(number)
    #print(f'Deleted number {number}')

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
def api_shorten():
    url = request.args.get('url')
    if not url_validate(url):
        return Response('Invalid string: not valid url.', 400)
    
    number = rng.randint(1, base**30)
    while number in url_addresses:
        number = rng.randint(1, base**30)
    _, shortened = convert_to_BASE64(number)
    #print(f'Created number {number} for code {shortened}')
    url_addresses[number] = url
    thread = Thread(target=lambda: delete_after(number, 1))
    thread.start()
    returned_url = f'{request.host_url}{shortened}'
    return {
        'url': returned_url
    }

@app.get('/<string:code>')
def redirect_to_url(code:str):
    if code == 'favicon.ico':
        return Response(status=500)

    valid, number = convert_from_BASE64(code)
    #print(f'Decoded code {code} as number {number}')

    if valid and number in url_addresses:
        response_url = url_addresses[number]
        #print(f'Redirecting to {response_url}')
        return Response(status=301, headers={
            'Location': response_url
        })
    else:
        return Response(f'Invalid code provided.', 400)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG, threaded=True)