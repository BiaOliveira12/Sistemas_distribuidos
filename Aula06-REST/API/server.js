var express = require('express');
var http = require('http');
var mysql = require('mysql');

var conn = mysql.createConnection( {
    host : "localhost" , 
    user : "root" ,
    password : "",
    database : "loja"
} );


var app = express();

app.get('/', (req, res) => { 
    res.status( 200 ).send( "Bem-vindo(a) à nossa API REST" );

});

http.createServer(app).listen(8001, () => {
    console.log( "Servidor iniciador em http://localhost:8001");
});