//Exercício: Criar no banco de dados a tabela cliente
// que deve conter as colunas id, nome, altura
// criar um endpoint para retornar os clientes ordenados pela altura

const express = require('express');
const mysql = require('mysql2');

const app = express();
const port = 3000;

const pool = mysql.createPool({
    host : "localhost" , 
    user : "root" ,
    password : "",
    database : "loja"
});

app.get('/clientes', (req, res) => {
    pool.query('SELECT * FROM cliente ORDER BY altura', (error, results) => {
        if (error) {
            console.error(error);
            res.status(500).send('Erro ao buscar clientes');
        } else {
            res.json(results);
        }
    });
});

app.listen(port, () => {
    console.log(`Servidor rodando em http://localhost:${port}`);
});
