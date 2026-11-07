// Local adapter for the same serverless handler deployed on Vercel.
import http from 'node:http';
import https from 'node:https';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import handler from '../api/workspace.js';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../dist');
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json','.glb':'model/gltf-binary','.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp','.svg':'image/svg+xml','.wasm':'application/wasm'};
const listener=async(req,res)=>{
  const url=new URL(req.url,'http://127.0.0.1');
  if(url.pathname==='/api/workspace'){
    let body='';for await(const c of req){body+=c;if(body.length>2200000){res.writeHead(413);res.end();return}}
    req.query=Object.fromEntries(url.searchParams);req.body=body||undefined;
    res.status=v=>{res.statusCode=v;return res};res.json=v=>{res.setHeader('Content-Type','application/json');res.end(JSON.stringify(v))};return handler(req,res);
  }
  try{const route=decodeURIComponent(url.pathname);if(route.split('/').some(p=>p.startsWith('.')&&p!==''))throw Error();const file=path.resolve(root,'.'+route+(route.endsWith('/')?'index.html':''));if(!file.startsWith(root+path.sep))throw Error();const data=await fs.readFile(file);res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');res.end(data)}catch{res.writeHead(404);res.end('Not found')}
};
const tls=process.argv.includes('--https');
const server=tls?https.createServer({key:await fs.readFile(path.resolve(root,'../.local/localhost-key.pem')),cert:await fs.readFile(path.resolve(root,'../.local/localhost-cert.pem'))},listener):http.createServer(listener);
server.listen(Number(process.env.PORT||5190),'127.0.0.1',()=>console.log(`Spatial cloud integration preview: ${tls?'https':'http'}://127.0.0.1:${server.address().port}`));
