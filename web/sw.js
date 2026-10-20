"use strict";
// Editing requires the studio computer. Never cache private media or API replies.
self.addEventListener("install",()=>self.skipWaiting());
self.addEventListener("activate",event=>event.waitUntil(self.clients.claim()));
self.addEventListener("fetch",event=>{
  if(event.request.mode==="navigate"){
    event.respondWith(fetch(event.request).catch(()=>new Response(
      '<!doctype html><html lang="pt-BR"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lili · Sem conexão</title><body style="background:#f7f6f2;color:#292d29;font:17px/1.6 system-ui;padding:40px;max-width:480px;margin:auto"><h1>Vamos reconectar?</h1><p>Verifique a internet e se o computador do estúdio está ligado.</p><a href="/">Tentar novamente</a></body></html>',
      {status:503,headers:{"Content-Type":"text/html; charset=utf-8","Cache-Control":"no-store"}})));
  }
});
