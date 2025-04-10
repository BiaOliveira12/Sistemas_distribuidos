const { setFips } = require('crypto');
var express = require('express');
var http = require('http');
const { connect } = require('http2');
var mysql = require('mysql');

var conn = mysql.createConnection( {
    host : "localhost" , 
    user : "root" ,
    password : "",
    database : "loja"
} );

try{
    if(conn.state != "authenticated"){
        conn.connect( function(erro){
            if(erro){
                console.log(erro);
            }
        } );
    }
}catch(error){
    console.log(erro);
}

var app = express();

app.get('/', (req, res) => { 
    res.status( 200 ).send( "Bem-vindo(a) à nossa API REST" );
});

app.get('/produto', (req, res) => { 
    res.statusCode = 200;
    res.setHeader('Content-Type', 'application/json');
    var sql = "SELECT * FROM produto ORDER BY nome";
    conn.query(sql, function(err, result, fields){
        if(err){
            res.send('{ "resposta": "Erro ao executar a consulta" }');
        }else{
            res.send(JSON.stringify(result));
        }
    }); 
});

http.createServer(app).listen(8001, () => {
    console.log( "Servidor iniciador em http://localhost:8001");
});